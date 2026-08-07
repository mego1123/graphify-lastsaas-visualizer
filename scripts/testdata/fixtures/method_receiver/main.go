package method_receiver

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
)

// Foo is a test struct with a method-receiver function.
type Foo struct {
	Name string `json:"name" bson:"name"`
}

// Bar is a second struct with a same-named method to test disambiguation.
type Bar struct {
	Email string `json:"email" bson:"email"`
}

// Process is a plain function (no receiver) — should match by exact label.
func Process(ctx context.Context) {
	_ = bson.M{"plainField": "value"}
}

// Filter is the method-receiver function the test looks for.
// The tracer will report this as (*Foo).Filter.
func (f *Foo) Filter(ctx context.Context) {
	_ = bson.M{"name": f.Name}
}

// Filter on Bar — same method name, different receiver.
// Tests that the enrich/query helpers correctly disambiguate
// (*Foo).Filter from (*Bar).Filter.
func (b *Bar) Filter(ctx context.Context) {
	_ = bson.M{"email": b.Email}
}
