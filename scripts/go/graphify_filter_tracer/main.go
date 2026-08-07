// graphify_filter_tracer uses golang.org/x/tools/go/ssa to trace which
// fields get written to bson.M / bson.D filter variables in functions
// that perform MongoDB operations.
//
// For each function that contains a call to one of:
//
//      Find, FindOne, FindOneAndUpdate, FindOneAndDelete, FindOneAndReplace,
//      UpdateOne, UpdateMany, DeleteOne, DeleteMany, InsertOne, InsertMany,
//      CountDocuments, Aggregate, ReplaceOne, BulkWrite
//
// it produces one or more Finding records describing how a filter (or
// document / update) was constructed:
//
//   - "literal"     — a bson.M{...} or bson.D{...} composite literal that
//                     has at least one key. Keys are extracted from the
//                     AST so that both map-style and bson.E-style literals
//                     are handled.
//   - "map_update"  — an explicit `filter["x"] = y` write discovered via
//                     ssa.MapUpdate. MapUpdates that are part of an
//                     inline bson.M{...} literal are deduplicated against
//     the "literal" pass using source positions, so they only appear once.
//   - "struct_type" — a Call to InsertOne / InsertMany / ReplaceOne whose
//                     document argument is a struct (or slice of structs).
//                     The reported fields are the bson tag names of the
//                     struct's fields (flattened through embedded structs).
//
// Output is a JSON array of FunctionReport objects, written to stdout or
// a file with -out.
//
// Usage:
//
//      cd /path/to/go/project && go run /path/to/graphify_filter_tracer/main.go -out filters.json
package main

import (
        "encoding/json"
        "flag"
        "fmt"
        "go/ast"
        "go/constant"
        "go/token"
        "go/types"
        "os"
        "path/filepath"
        "reflect"
        "sort"
        "strconv"
        "strings"

        "golang.org/x/tools/go/packages"
        "golang.org/x/tools/go/ssa"
        "golang.org/x/tools/go/ssa/ssautil"
)

// Finding describes one observation of how a filter / document was
// constructed inside a function.
type Finding struct {
        Method     string   `json:"method"`               // literal | map_update | struct_type
        Operation  string   `json:"operation,omitempty"`  // Find, FindOne, InsertOne, ...
        Fields     []string `json:"fields"`                // extracted field names
        StructType string  `json:"structType,omitempty"`  // for struct_type, e.g. "models.User"
        Variable   string   `json:"variable,omitempty"`    // for map_update, the map variable name (best-effort)
        Position   string   `json:"position"`              // file:line
}

// FunctionReport aggregates findings for one function.
type FunctionReport struct {
        Function string    `json:"function"`
        Package  string    `json:"package"`
        File     string    `json:"file"`
        Line     int       `json:"line"`
        Findings []Finding `json:"findings"`
}

// Config holds CLI options.
type Config struct {
        Out      string
        Patterns []string
        Verbose  bool
        Tests    bool
}

// mongoOps is the set of method names we treat as MongoDB operations.
// The first occurrence of any of these inside a function marks that
// function as "interesting".
var mongoOps = map[string]bool{
        "Find":              true,
        "FindOne":           true,
        "FindOneAndUpdate":  true,
        "FindOneAndDelete":  true,
        "FindOneAndReplace": true,
        "UpdateOne":         true,
        "UpdateMany":        true,
        "DeleteOne":         true,
        "DeleteMany":        true,
        "InsertOne":         true,
        "InsertMany":        true,
        "CountDocuments":    true,
        "Aggregate":         true,
        "ReplaceOne":        true,
        "BulkWrite":         true,
}

// methodsWhoseArg1IsFilter lists mongo ops where Args[dataArgIdx] is a
// filter (not a document / pipeline).
var methodsWhoseArg1IsFilter = map[string]bool{
        "Find": true, "FindOne": true,
        "FindOneAndUpdate": true, "FindOneAndDelete": true, "FindOneAndReplace": true,
        "UpdateOne": true, "UpdateMany": true,
        "DeleteOne": true, "DeleteMany": true,
        "CountDocuments": true, "ReplaceOne": true,
}

// methodsWhoseArg1IsDocument lists mongo ops where Args[dataArgIdx] is a
// document (struct / map) being inserted or replaced — these are the
// candidates for the struct_type pass.
var methodsWhoseArg1IsDocument = map[string]bool{
        "InsertOne": true, "InsertMany": true, "ReplaceOne": true,
        "FindOneAndReplace": true,
}

func main() {
        var (
                out     = flag.String("out", "", "write JSON output to this file instead of stdout")
                verbose = flag.Bool("v", false, "emit progress to stderr")
                tests   = flag.Bool("tests", false, "include _test.go files")
        )
        flag.Usage = func() {
                fmt.Fprintln(os.Stderr, "usage: graphify_filter_tracer [-out FILE] [-v] [-tests] [PATTERN ...]")
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

        // Build SSA only for the initial packages (deps=false). Dependency
        // packages get placeholder SSA packages with no instructions, which
        // is fine — we only walk the initial set's functions.
        prog, ssaPkgs := ssautil.Packages(pkgs, ssa.InstantiateGenerics)
        prog.Build()
        if cfg.Verbose {
                fmt.Fprintf(os.Stderr, "built SSA for %d packages\n", len(ssaPkgs))
        }

        // Map types.Package -> bool for the initial set, so we can filter
        // out functions belonging to dependencies.
        initial := make(map[*types.Package]bool)
        // Map types.Package -> *types.Info so the AST pass can do precise
        // type resolution (e.g. detect `map[string]interface{}` literals
        // that aren't typed as bson.M).
        infoByPkg := make(map[*types.Package]*types.Info)
        for _, p := range pkgs {
                if p.Types != nil {
                        initial[p.Types] = true
                        if p.TypesInfo != nil {
                                infoByPkg[p.Types] = p.TypesInfo
                        }
                }
        }

        fset := prog.Fset
        reports := []FunctionReport{}

        for fn := range ssautil.AllFunctions(prog) {
                // Skip synthetic functions (anonymous wrappers, init wrappers,
                // interface thunks, etc.) — they have no source-level object.
                if fn.Object() == nil {
                        continue
                }
                // Skip functions from dependency packages.
                pkg := fn.Package()
                if pkg == nil || pkg.Pkg == nil || !initial[pkg.Pkg] {
                        continue
                }
                // Skip functions with no body (e.g. extern declarations).
                if fn.Blocks == nil || len(fn.Blocks) == 0 {
                        continue
                }

                // Determine whether this function calls any mongo op. While
                // doing so, collect the call sites so we can later attribute
                // findings to specific operations.
                mongoCalls := collectMongoCalls(fn)
                if len(mongoCalls) == 0 {
                        continue
                }

                pos := fset.Position(fn.Pos())
                rpt := FunctionReport{
                        Function: fn.RelString(pkg.Pkg),
                        Package:  pkg.Pkg.Path(),
                        File:     relPath(pos.Filename),
                        Line:     pos.Line,
                        Findings: []Finding{},
                }

                info := infoByPkg[pkg.Pkg]

                // Pass 1: AST scan for bson.M{...} / bson.D{...} / map[string]any{}
                // literals. Records source ranges of all matched literals so the
                // MapUpdate pass can dedupe inline-construction updates.
                literalRanges := scanLiterals(fn, info, fset, &rpt)

                // Pass 2: SSA scan for MapUpdates on bson.M-typed maps.
                scanMapUpdates(fn, fset, literalRanges, &rpt)

                // Pass 3: SSA scan for struct-typed args to InsertOne / etc.
                scanStructArgs(fn, fset, mongoCalls, &rpt)

                // Only emit reports for functions that produced at least one
                // finding OR explicitly call a mongo op (so callers can see
                // "this function uses Mongo but we couldn't extract a filter").
                if len(rpt.Findings) > 0 {
                        reports = append(reports, rpt)
                }
        }

        // Stable ordering.
        sort.Slice(reports, func(i, j int) bool {
                if reports[i].Package != reports[j].Package {
                        return reports[i].Package < reports[j].Package
                }
                if reports[i].File != reports[j].File {
                        return reports[i].File < reports[j].File
                }
                return reports[i].Line < reports[j].Line
        })

        if cfg.Verbose {
                total := 0
                for _, r := range reports {
                        total += len(r.Findings)
                }
                fmt.Fprintf(os.Stderr, "emitted %d findings across %d functions\n", total, len(reports))
        }

        buf, err := json.MarshalIndent(reports, "", "  ")
        if err != nil {
                return fmt.Errorf("marshal: %w", err)
        }
        if cfg.Out != "" {
                if err := os.WriteFile(cfg.Out, buf, 0o644); err != nil {
                        return fmt.Errorf("write %s: %w", cfg.Out, err)
                }
                if cfg.Verbose {
                        fmt.Fprintf(os.Stderr, "wrote %s (%d bytes)\n", cfg.Out, len(buf))
                }
                return nil
        }
        _, _ = os.Stdout.Write(buf)
        _, _ = os.Stdout.Write([]byte("\n"))
        return nil
}

// mongoCall is a recorded call to one of the MongoDB operations.
type mongoCall struct {
        op   string         // method name, e.g. "Find"
        call *ssa.Call      // the SSA call instruction
        pos  token.Position // position of the call
}

// collectMongoCalls walks every block of fn looking for *ssa.Call
// instructions whose callee (static or invoked) matches one of the
// MongoDB operation names.
func collectMongoCalls(fn *ssa.Function) []mongoCall {
        var out []mongoCall
        for _, b := range fn.Blocks {
                for _, instr := range b.Instrs {
                        call, ok := instr.(*ssa.Call)
                        if !ok {
                                continue
                        }
                        cc := call.Common()
                        name := ""
                        if cc.IsInvoke() {
                                name = cc.Method.Name()
                        } else if f := cc.StaticCallee(); f != nil {
                                name = f.Name()
                        }
                        if name == "" || !mongoOps[name] {
                                continue
                        }
                        out = append(out, mongoCall{
                                op:   name,
                                call: call,
                                pos:  fn.Prog.Fset.Position(cc.Pos()),
                        })
                }
        }
        return out
}

// scanLiterals walks the AST of fn's body looking for composite literals
// whose type is bson.M, bson.D, or map[string]interface{} (the underlying
// type of bson.M). For each non-empty literal it emits a "literal"
// finding with the field keys. It also returns the source ranges of ALL
// matched literals (including empty ones) so the MapUpdate pass can skip
// updates that belong to a literal construction.
//
// Detection uses TypesInfo for precise type resolution when available,
// falling back to AST identifier matching (bson.M / bson.D) so the tool
// still works on packages whose TypesInfo is incomplete.
func scanLiterals(fn *ssa.Function, info *types.Info, fset *token.FileSet, rpt *FunctionReport) []literalRange {
        ranges := []literalRange{}
        syn := fn.Syntax()
        if syn == nil {
                return ranges
        }
        ast.Inspect(syn, func(n ast.Node) bool {
                lit, ok := n.(*ast.CompositeLit)
                if !ok {
                        return true
                }
                bsonKind := classifyLiteral(lit, info)
                if bsonKind == "" {
                        return true
                }
                // Record the literal's source range so the SSA MapUpdate
                // pass can skip updates that belong to this literal. This is
                // done for empty literals too, even though they have no
                // MapUpdates of their own — symmetry is cheap.
                start := fset.Position(lit.Pos())
                end := fset.Position(lit.End())
                ranges = append(ranges, literalRange{
                        file:  start.Filename,
                        start: start.Offset,
                        end:   end.Offset,
                })
                if len(lit.Elts) == 0 {
                        return true
                }
                keys := extractLiteralKeys(bsonKind, lit)
                if len(keys) == 0 {
                        return true
                }
                // Find the nearest enclosing *ast.CallExpr whose callee name
                // is a mongo op (best-effort).
                op := enclosingMongoOp(fn, lit)
                rpt.Findings = append(rpt.Findings, Finding{
                        Method:    "literal",
                        Operation: op,
                        Fields:    keys,
                        Position:  fmt.Sprintf("%s:%d", relPath(start.Filename), start.Line),
                })
                return true
        })
        return ranges
}

// classifyLiteral returns "M" if lit's type is bson.M or
// map[string]interface{} (the underlying type of bson.M), "D" if it's
// bson.D, and "" otherwise.
func classifyLiteral(lit *ast.CompositeLit, info *types.Info) string {
        // Try precise type resolution first.
        if info != nil {
                if tv, ok := info.Types[lit]; ok {
                        return classifyType(tv.Type)
                }
                // Some literals don't have a Types entry but do have an
                // inferred type via their Type expression.
                if lit.Type != nil {
                        if tv, ok := info.Types[lit.Type]; ok {
                                return classifyType(tv.Type)
                        }
                }
        }
        // Fall back to identifier name matching.
        return matchBsonIdent(lit.Type)
}

// classifyType inspects a types.Type and returns "M", "D", or "".
//
// Handles *types.Named (e.g. primitive.Regex), *types.Alias (e.g.
// bson.M which is `type M = map[string]interface{}`), and the raw
// underlying types (map[string]interface{} for M, []bson.E for D).
func classifyType(t types.Type) string {
        switch v := t.(type) {
        case *types.Alias:
                obj := v.Obj()
                if obj.Pkg() != nil && obj.Pkg().Path() == "go.mongodb.org/mongo-driver/bson" {
                        switch obj.Name() {
                        case "M":
                                return "M"
                        case "D":
                                return "D"
                        }
                }
                return classifyType(v.Underlying())
        case *types.Named:
                obj := v.Obj()
                if obj.Pkg() != nil && obj.Pkg().Path() == "go.mongodb.org/mongo-driver/bson" {
                        switch obj.Name() {
                        case "M":
                                return "M"
                        case "D":
                                return "D"
                        case "E":
                                // bson.E is the element type of bson.D; the literal
                                // itself is reported as bson.E but it's part of a
                                // bson.D slice. We return "" here so callers don't
                                // mis-classify a bare bson.E as a top-level filter.
                                return ""
                        }
                }
                return classifyType(v.Underlying())
        case *types.Map:
                // map[string]interface{} (or map[string]any) — the underlying
                // type of bson.M.
                basic, ok := v.Key().(*types.Basic)
                if !ok || basic.Kind() != types.String {
                        return ""
                }
                if iface, ok := v.Elem().(*types.Interface); ok && iface.NumMethods() == 0 {
                        return "M"
                }
        case *types.Slice:
                // []bson.E — the underlying type of bson.D.
                if named, ok := v.Elem().(*types.Named); ok {
                        obj := named.Obj()
                        if obj.Pkg() != nil && obj.Pkg().Path() == "go.mongodb.org/mongo-driver/bson" && obj.Name() == "E" {
                                return "D"
                        }
                }
                if alias, ok := v.Elem().(*types.Alias); ok {
                        obj := alias.Obj()
                        if obj.Pkg() != nil && obj.Pkg().Path() == "go.mongodb.org/mongo-driver/bson" && obj.Name() == "E" {
                                return "D"
                        }
                }
        }
        return ""
}

// literalRange is the [start, end) byte-offset range of a composite
// literal in a specific file, used to deduplicate MapUpdates.
type literalRange struct {
        file       string
        start, end int
}

// matchBsonIdent returns "M" if the AST type expression is the
// identifier `bson.M` (or `M` qualified by a `bson.` selector), "D" if
// it's `bson.D`, and "" otherwise.
func matchBsonIdent(typeExpr ast.Expr) string {
        if typeExpr == nil {
                return ""
        }
        switch t := typeExpr.(type) {
        case *ast.SelectorExpr:
                if ident, ok := t.X.(*ast.Ident); ok {
                        return matchBsonName(ident.Name, t.Sel.Name)
                }
        case *ast.Ident:
                return matchBsonName("", t.Name)
        }
        return ""
}

// matchBsonName returns "M" for a `bson.M` / `M` qualifier, "D" for
// `bson.D` / `D`, and "" otherwise.
func matchBsonName(pkg, name string) string {
        switch name {
        case "M":
                if pkg == "" || pkg == "bson" {
                        return "M"
                }
        case "D":
                if pkg == "" || pkg == "bson" {
                        return "D"
                }
        }
        return ""
}

// extractLiteralKeys pulls the field names out of a bson.M or bson.D
// composite literal. For bson.M (map literal), each element is a
// *ast.KeyValueExpr whose Key is a string literal. For bson.D (slice of
// bson.E), each element is itself a *ast.CompositeLit with a `Key: "..."`
// field.
func extractLiteralKeys(bsonKind string, lit *ast.CompositeLit) []string {
        keys := []string{}
        for _, el := range lit.Elts {
                switch bsonKind {
                case "M":
                        kv, ok := el.(*ast.KeyValueExpr)
                        if !ok {
                                continue
                        }
                        k := stringLiteral(kv.Key)
                        if k != "" {
                                keys = append(keys, k)
                        }
                case "D":
                        // Each element should be a *ast.CompositeLit (bson.E).
                        cl, ok := el.(*ast.CompositeLit)
                        if !ok {
                                // Could also be a *ast.KeyValueExpr in some
                                // shorthand forms — try anyway.
                                if kv, ok := el.(*ast.KeyValueExpr); ok {
                                        if k := stringLiteral(kv.Key); k != "" {
                                                keys = append(keys, k)
                                        }
                                }
                                continue
                        }
                        k := bsonEKey(cl)
                        if k != "" {
                                keys = append(keys, k)
                        }
                }
        }
        return keys
}

// bsonEKey looks at a *ast.CompositeLit of type bson.E and returns the
// value of the `Key: "..."` field. Both `bson.E{Key: "x", Value: y}`
// and positional `{Key: "x", Value: y}` forms are handled.
func bsonEKey(cl *ast.CompositeLit) string {
        // Named-field form.
        for _, el := range cl.Elts {
                kv, ok := el.(*ast.KeyValueExpr)
                if !ok {
                        continue
                }
                key, ok := kv.Key.(*ast.Ident)
                if !ok || key.Name != "Key" {
                        continue
                }
                if s := stringLiteral(kv.Value); s != "" {
                        return s
                }
        }
        // Positional form: bson.E{"x", y} — Key is element 0.
        if len(cl.Elts) > 0 {
                if s := stringLiteral(cl.Elts[0]); s != "" {
                        return s
                }
        }
        return ""
}

// stringLiteral returns the unquoted string value of an *ast.BasicLit
// of kind STRING, or "" if expr is not a string literal. Both
// double-quoted ("...") and back-quoted (`...`) forms are handled.
func stringLiteral(expr ast.Expr) string {
        lit, ok := expr.(*ast.BasicLit)
        if !ok || lit.Kind != token.STRING {
                return ""
        }
        s, err := strconv.Unquote(lit.Value)
        if err != nil {
                // strconv.Unquote only handles double-quoted strings; fall
                // back to stripping backticks.
                v := lit.Value
                if len(v) >= 2 && v[0] == '`' && v[len(v)-1] == '`' {
                        return v[1 : len(v)-1]
                }
                return ""
        }
        return s
}

// enclosingMongoOp walks up the AST stack maintained by an outer
// ast.Inspect call to find the nearest enclosing *ast.CallExpr whose
// callee is a method matching one of the mongo op names. Because
// ast.Inspect doesn't expose the parent chain, we re-walk the whole
// function and check whether the literal's position is inside the call's
// argument list.
func enclosingMongoOp(fn *ssa.Function, target ast.Node) string {
        syn := fn.Syntax()
        if syn == nil {
                return ""
        }
        fset := fn.Prog.Fset
        tpos := fset.Position(target.Pos())
        tend := fset.Position(target.End())

        best := ""
        bestStart := -1

        ast.Inspect(syn, func(n ast.Node) bool {
                call, ok := n.(*ast.CallExpr)
                if !ok {
                        return true
                }
                name := callMethodName(call.Fun)
                if name == "" || !mongoOps[name] {
                        return true
                }
                cpos := fset.Position(call.Pos())
                cend := fset.Position(call.End())
                // Is the literal inside this call's argument list?
                if tpos.Filename == cpos.Filename &&
                        tpos.Offset >= cpos.Offset && tend.Offset <= cend.Offset {
                        // Pick the *innermost* matching call.
                        if bestStart == -1 || cpos.Offset > bestStart {
                                bestStart = cpos.Offset
                                best = name
                        }
                }
                return true
        })
        return best
}

// callMethodName returns the method name from a call's Fun expression.
// Handles `x.Method(...)`, `x.Method().InnerMethod(...)`, and bare
// `Method(...)` calls.
func callMethodName(fun ast.Expr) string {
        sel, ok := fun.(*ast.SelectorExpr)
        if !ok {
                return ""
        }
        return sel.Sel.Name
}

// scanMapUpdates walks the SSA blocks of fn and emits one "map_update"
// finding for each ssa.MapUpdate whose Map's type is bson.M
// (map[string]interface{}). MapUpdates whose position falls inside a
// bson.M / bson.D / map[string]interface{} literal's source range (as
// recorded by scanLiterals) are skipped — they are part of the literal
// construction and are already reported (or skipped) as literals. Only
// explicit user-written mutations like `filter["x"] = y` survive.
func scanMapUpdates(fn *ssa.Function, fset *token.FileSet, literalRanges []literalRange, rpt *FunctionReport) {
        for _, b := range fn.Blocks {
                for _, instr := range b.Instrs {
                        upd, ok := instr.(*ssa.MapUpdate)
                        if !ok {
                                continue
                        }
                        if !isBsonM(upd.Map.Type()) {
                                continue
                        }
                        pos := fset.Position(upd.Pos())
                        // Skip if this update is inside a literal we already reported
                        // or recorded as a range (e.g. `filter := bson.M{...}` whose
                        // construction SSA lowers into MakeMap + MapUpdates).
                        if inAnyRange(literalRanges, pos) {
                                continue
                        }
                        key := constString(upd.Key)
                        rpt.Findings = append(rpt.Findings, Finding{
                                Method:    "map_update",
                                Fields:    []string{key},
                                Variable:  valueName(upd.Map),
                                Position:  fmt.Sprintf("%s:%d", relPath(pos.Filename), pos.Line),
                        })
                }
        }
}

// scanStructArgs walks the SSA blocks of fn looking for calls to
// InsertOne / InsertMany / ReplaceOne (and friends) whose document
// argument is a struct (or slice of structs). For each, it emits a
// "struct_type" finding with the struct's bson-tagged field names.
func scanStructArgs(fn *ssa.Function, fset *token.FileSet, calls []mongoCall, rpt *FunctionReport) {
        for _, mc := range calls {
                if !methodsWhoseArg1IsDocument[mc.op] {
                        continue
                }
                cc := mc.call.Common()
                argIdx := dataArgIndex(cc)
                if argIdx < 0 || argIdx >= len(cc.Args) {
                        continue
                }
                arg := cc.Args[argIdx]
                t := concreteType(arg)
                if t == nil {
                        continue
                }
                // Unwrap pointer types.
                if ptr, ok := t.(*types.Pointer); ok {
                        t = ptr.Elem()
                }
                // Unwrap named types.
                named, _ := t.(*types.Named)
                var structType *types.Struct
                var sliceElem types.Type
                if s, ok := t.Underlying().(*types.Struct); ok {
                        structType = s
                } else if sl, ok := t.Underlying().(*types.Slice); ok {
                        sliceElem = sl.Elem()
                        if ptr, ok := sliceElem.(*types.Pointer); ok {
                                sliceElem = ptr.Elem()
                        }
                        if s, ok := sliceElem.Underlying().(*types.Struct); ok {
                                structType = s
                        }
                }
                if structType == nil {
                        continue
                }
                typeName := typeString(t)
                if typeName == "" && named != nil {
                        typeName = named.Obj().Pkg().Path() + "." + named.Obj().Name()
                }
                rpt.Findings = append(rpt.Findings, Finding{
                        Method:     "struct_type",
                        Operation:  mc.op,
                        StructType: typeName,
                        Fields:     structBsonFields(structType),
                        Position:   fmt.Sprintf("%s:%d", relPath(mc.pos.Filename), mc.pos.Line),
                })
        }
}

// concreteType returns the concrete type of v, unwrapping *ssa.MakeInterface
// (which boxes a concrete value into an empty interface). For other Value
// kinds it returns v.Type() as-is.
func concreteType(v ssa.Value) types.Type {
        if mi, ok := v.(*ssa.MakeInterface); ok {
                return mi.X.Type()
        }
        return v.Type()
}

// dataArgIndex returns the index in CallCommon.Args of the "data"
// argument (filter, document, or pipeline) for a mongo-op call. For
// static calls to methods, Args[0] is the receiver, Args[1] is ctx,
// Args[2] is the data arg. For invoke-mode calls (interface methods),
// Args[0] is ctx, Args[1] is the data arg.
func dataArgIndex(cc *ssa.CallCommon) int {
        if cc.IsInvoke() {
                return 1
        }
        if f := cc.StaticCallee(); f != nil {
                if f.Signature != nil && f.Signature.Recv() != nil {
                        return 2
                }
                return 1
        }
        return 1
}

// isBsonM reports whether t is the underlying type of bson.M, i.e.
// map[string]interface{} (which is map[string]<any interface>).
// Type aliases (e.g. bson.M itself, which is `type M = map[string]any`)
// are unwrapped first.
func isBsonM(t types.Type) bool {
        // Unwrap type aliases (Go 1.22+ represents `type M = ...` as
        // *types.Alias when GOEXPERIMENT=aliastypes or go >= 1.25).
        if alias, ok := t.(*types.Alias); ok {
                t = alias.Underlying()
        }
        m, ok := t.(*types.Map)
        if !ok {
                return false
        }
        // Key must be string.
        basic, ok := m.Key().(*types.Basic)
        if !ok || basic.Kind() != types.String {
                return false
        }
        // Element must be interface{} (empty interface).
        iface, ok := m.Elem().(*types.Interface)
        if !ok {
                return false
        }
        return iface.NumMethods() == 0
}

// constString returns the string value of v if v is an *ssa.Const
// holding a string, otherwise "<dynamic>".
func constString(v ssa.Value) string {
        if c, ok := v.(*ssa.Const); ok && c.Value != nil {
                // constant.StringVal only returns a meaningful result for
                // string constants; for everything else it returns "".
                if c.Value.Kind() == constant.String {
                        return constant.StringVal(c.Value)
                }
        }
        return "<dynamic>"
}

// valueName returns a best-effort human-readable name for an SSA value
// (e.g. "filter" for a *ssa.Alloc with Name() "filter"). Used to label
// map_update findings so the Python caller can correlate mutations
// across multiple findings.
func valueName(v ssa.Value) string {
        switch x := v.(type) {
        case *ssa.Alloc:
                return x.Comment
        case *ssa.Parameter:
                return x.Name()
        case *ssa.MakeMap:
                return "<literal>"
        }
        return ""
}

// inAnyRange reports whether pos falls inside any of the literalRanges.
func inAnyRange(ranges []literalRange, pos token.Position) bool {
        for _, r := range ranges {
                if pos.Filename == r.file &&
                        pos.Offset >= r.start && pos.Offset < r.end {
                        return true
                }
        }
        return false
}

// structBsonFields returns the bson tag names of all fields of s
// (recursively flattened through embedded structs).
func structBsonFields(s *types.Struct) []string {
        out := []string{}
        for i := 0; i < s.NumFields(); i++ {
                f := s.Field(i)
                tag := s.Tag(i)
                if f.Embedded() {
                        t := f.Type()
                        if ptr, ok := t.(*types.Pointer); ok {
                                t = ptr.Elem()
                        }
                        if named, ok := t.(*types.Named); ok {
                                t = named.Underlying()
                        }
                        if embedded, ok := t.(*types.Struct); ok {
                                out = append(out, structBsonFields(embedded)...)
                                continue
                        }
                }
                name := parseTag(tag, "bson")
                if name == "" {
                        name = f.Name()
                }
                out = append(out, name)
        }
        return out
}

// parseTag is the same helper used by the struct_flattener tool. It
// uses reflect.StructTag for canonical parsing.
func parseTag(tag, key string) string {
        if tag == "" {
                return ""
        }
        v := reflect.StructTag(tag).Get(key)
        if v == "" {
                return ""
        }
        if i := strings.IndexByte(v, ','); i >= 0 {
                v = v[:i]
        }
        return v
}

// typeString renders a types.Type as a package-qualified name where
// possible. Used for the structType field of struct_type findings.
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
        case *types.Slice:
                return "[]" + typeString(v.Elem())
        default:
                return t.String()
        }
}

// relPath converts an absolute file path to one relative to the current
// working directory (which, by contract, is the Go module root).
func relPath(p string) string {
        if p == "" {
                return ""
        }
        abs, err := filepath.Abs(p)
        if err != nil {
                return p
        }
        wd, err := os.Getwd()
        if err != nil {
                return p
        }
        rel, err := filepath.Rel(wd, abs)
        if err != nil || strings.HasPrefix(rel, "..") {
                return p
        }
        return rel
}
