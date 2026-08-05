// graphify_struct_flattener loads a Go module with go/packages, walks every
// type declaration, flattens struct fields (recursively resolving embedded
// structs), and emits a JSON array of StructInfo records to stdout (or a
// file with -out).
//
// It is designed to be invoked as a subprocess from a Python analyzer:
//
//      cd /path/to/go/project && go run /path/to/graphify_struct_flattener/main.go -out structs.json
//
// The output schema is:
//
//      [
//        {
//          "name": "User",
//          "package": "lastsaas/internal/models",
//          "file": "internal/models/user.go",
//          "fields": [
//            {"name": "ID", "jsonName": "id", "bsonName": "_id", "type": "primitive.ObjectID", "embedded": false, "tag": "..."},
//            ...
//          ]
//        },
//        ...
//      ]
package main

import (
        "encoding/json"
        "flag"
        "fmt"
        "go/types"
        "os"
        "path/filepath"
        "reflect"
        "sort"
        "strings"

        "golang.org/x/tools/go/packages"
)

// FieldInfo describes a single (flattened) struct field.
type FieldInfo struct {
        Name     string `json:"name"`
        JSONName string `json:"jsonName"`
        BSONName string `json:"bsonName"`
        Type     string `json:"type"`
        Embedded bool   `json:"embedded"`
        Tag      string `json:"tag,omitempty"`
}

// StructInfo describes one struct type and all of its (flattened) fields.
type StructInfo struct {
        Name    string      `json:"name"`
        Package string      `json:"package"`
        File    string      `json:"file"`
        Fields  []FieldInfo `json:"fields"`
}

// Config holds the runtime knobs parsed from CLI flags.
type Config struct {
        Out      string
        Patterns []string
        Verbose  bool
        Tests    bool
}

func main() {
        var (
                out     = flag.String("out", "", "write JSON output to this file instead of stdout")
                verbose = flag.Bool("v", false, "emit progress to stderr")
                tests   = flag.Bool("tests", false, "include _test.go files")
        )
        flag.Usage = func() {
                fmt.Fprintln(os.Stderr, "usage: graphify_struct_flattener [-out FILE] [-v] [-tests] [PATTERN ...]")
                fmt.Fprintln(os.Stderr, "")
                fmt.Fprintln(os.Stderr, "PATTERN defaults to \"./...\". Run from the root of the Go module you want to analyze.")
                flag.PrintDefaults()
        }
        flag.Parse()

        cfg := Config{
                Out:      *out,
                Patterns: flag.Args(),
                Verbose:  *verbose,
                Tests:    *tests,
        }
        if len(cfg.Patterns) == 0 {
                cfg.Patterns = []string{"./..."}
        }

        if err := run(cfg); err != nil {
                fmt.Fprintf(os.Stderr, "error: %v\n", err)
                os.Exit(1)
        }
}

func run(cfg Config) error {
        if cfg.Verbose {
                fmt.Fprintf(os.Stderr, "loading packages: %v\n", cfg.Patterns)
        }

        mode := packages.NeedName | packages.NeedFiles | packages.NeedTypes |
                packages.NeedTypesInfo | packages.NeedSyntax | packages.NeedDeps |
                packages.NeedImports | packages.NeedModule

        pkgs, err := packages.Load(&packages.Config{
                Mode:       mode,
                Tests:      cfg.Tests,
                BuildFlags: []string{"-tags=!ignore"},
        }, cfg.Patterns...)
        if err != nil {
                return fmt.Errorf("packages.Load: %w", err)
        }

        // Report load errors to stderr but keep going — partial results are
        // still useful.
        var loadErrs int
        for _, p := range pkgs {
                for _, e := range p.Errors {
                        loadErrs++
                        if cfg.Verbose {
                                fmt.Fprintf(os.Stderr, "  pkg %s: %v\n", p.ID, e)
                        }
                }
        }
        if cfg.Verbose {
                fmt.Fprintf(os.Stderr, "loaded %d packages (%d errors)\n", len(pkgs), loadErrs)
        }

        // De-duplicate struct types by (pkgpath, name) — a struct can be
        // reachable through multiple package nodes (e.g. when vendored or
        // imported via test variants).
        seen := make(map[string]bool)
        var out []StructInfo

        for _, p := range pkgs {
                if p.Types == nil {
                        continue
                }
                pkgPath := p.Types.Path()
                if cfg.Verbose {
                        fmt.Fprintf(os.Stderr, "scanning package %s (%d files)\n", pkgPath, len(p.Syntax))
                }
                scope := p.Types.Scope()
                // Stable iteration over the type names.
                names := scope.Names()
                sort.Strings(names)
                for _, name := range names {
                        obj := scope.Lookup(name)
                        tname, ok := obj.(*types.TypeName)
                        if !ok {
                                continue
                        }
                        named, ok := tname.Type().(*types.Named)
                        if !ok {
                                // Skip type aliases / built-ins.
                                continue
                        }
                        s, ok := named.Underlying().(*types.Struct)
                        if !ok {
                                continue
                        }
                        key := pkgPath + "." + name
                        if seen[key] {
                                continue
                        }
                        seen[key] = true

                        file := fileForType(p, tname)
                        info := StructInfo{
                                Name:    name,
                                Package: pkgPath,
                                File:    file,
                                Fields:  flattenFields(s),
                        }
                        out = append(out, info)
                }
        }

        if cfg.Verbose {
                fmt.Fprintf(os.Stderr, "found %d structs\n", len(out))
        }

        // Stable output ordering.
        sort.Slice(out, func(i, j int) bool {
                if out[i].Package != out[j].Package {
                        return out[i].Package < out[j].Package
                }
                return out[i].Name < out[j].Name
        })

        buf, err := json.MarshalIndent(out, "", "  ")
        if err != nil {
                return fmt.Errorf("marshal: %w", err)
        }

        if cfg.Out != "" {
                if err := os.WriteFile(cfg.Out, buf, 0o644); err != nil {
                        return fmt.Errorf("write %s: %w", cfg.Out, err)
                }
                if cfg.Verbose {
                        fmt.Fprintf(os.Stderr, "wrote %s (%d bytes, %d structs)\n", cfg.Out, len(buf), len(out))
                }
                return nil
        }
        _, _ = os.Stdout.Write(buf)
        _, _ = os.Stdout.Write([]byte("\n"))
        return nil
}

// flattenFields recursively walks a struct, inlining the fields of any
// embedded named struct. Pointer-typed embedded structs are also followed
// (the *types.Pointer is unwrapped to reach the underlying *types.Struct).
// Non-struct embedded fields (e.g. embedded time.Time — but time.Time is
// itself a struct so this branch is rarely hit) are emitted as a regular
// field with Embedded=true.
func flattenFields(s *types.Struct) []FieldInfo {
        fields := []FieldInfo{}
        for i := 0; i < s.NumFields(); i++ {
                f := s.Field(i)
                tag := s.Tag(i) // raw struct tag string, e.g. `json:"id" bson:"_id"`
                if f.Embedded() {
                        t := f.Type()
                        // Drill through *types.Pointer and *types.Named to find
                        // the underlying struct.
                        if ptr, ok := t.(*types.Pointer); ok {
                                t = ptr.Elem()
                        }
                        if named, ok := t.(*types.Named); ok {
                                t = named.Underlying()
                        }
                        if embedded, ok := t.(*types.Struct); ok {
                                fields = append(fields, flattenFields(embedded)...)
                                continue
                        }
                }
                fields = append(fields, FieldInfo{
                        Name:     f.Name(),
                        JSONName: parseTag(tag, "json", f.Name()),
                        BSONName: parseTag(tag, "bson", f.Name()),
                        Type:     typeString(f.Type()),
                        Embedded: f.Embedded(),
                        Tag:      tag,
                })
        }
        return fields
}

// parseTag parses a struct tag (the raw string literal from
// (*types.Var).Tag()) and returns the value for the named key, or the
// fallback if missing. The "name" portion of a tag (the part before the
// first comma) is returned; "omitempty" and friends are dropped.
func parseTag(tag, key, fallback string) string {
        if tag == "" {
                return ""
        }
        // Use reflect.StructTag for canonical parsing — it correctly handles
        // quoted values containing colons.
        v := reflect.StructTag(tag).Get(key)
        if v == "" {
                return ""
        }
        // "fieldName,omitempty" -> "fieldName"
        if i := strings.IndexByte(v, ','); i >= 0 {
                v = v[:i]
        }
        if v == "-" {
                // "-" means "do not serialize" in both json and bson conventions.
                return "-"
        }
        if v == "" {
                return fallback
        }
        return v
}

// typeString produces a stable, human-readable name for a types.Type.
// Named types are rendered as "pkg/path.Name"; pointer types get a "*"
// prefix; other types fall back to String().
func typeString(t types.Type) string {
        switch v := t.(type) {
        case *types.Named:
                obj := v.Obj()
                pkg := obj.Pkg()
                if pkg == nil {
                        return obj.Name()
                }
                return pkg.Path() + "." + obj.Name()
        case *types.Pointer:
                return "*" + typeString(v.Elem())
        default:
                return t.String()
        }
}

// fileForType returns the file path (relative to the module root) in which
// the given type name was declared. It uses the AST file set and the
// position of the TypeName's Pos().
func fileForType(p *packages.Package, tname *types.TypeName) string {
        if p.Fset == nil {
                return ""
        }
        pos := p.Fset.Position(tname.Pos())
        if pos.Filename == "" {
                return ""
        }
        // Try to make the path relative to the working directory (which, by
        // contract, is the root of the analyzed Go module). This matches how
        // the Python analyzers refer to files elsewhere in the workspace.
        if abs, err := filepath.Abs(pos.Filename); err == nil {
                if wd, err := os.Getwd(); err == nil {
                        if rel, err := filepath.Rel(wd, abs); err == nil && !strings.HasPrefix(rel, "..") {
                                return rel
                        }
                }
        }
        return pos.Filename
}
