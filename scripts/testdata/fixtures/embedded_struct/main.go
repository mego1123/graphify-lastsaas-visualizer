package embedded_struct

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
)

// BaseResponse is the embedded struct.
type BaseResponse struct {
	ID       string `json:"id" bson:"_id"`
	TenantID string `json:"tenantId" bson:"tenantId"`
}

// Tenant extends BaseResponse via embedding.
// The struct flattener should resolve fields from BaseResponse.
type Tenant struct {
	BaseResponse // embedded (value receiver)
	Name         string `json:"name" bson:"name"`
}

// PointerTenant extends *BaseResponse via pointer embedding.
type PointerTenant struct {
	*BaseResponse // pointer embedding
	Email         string `json:"email" bson:"email"`
}

// MultiLevelTenant tests multi-level embedding.
type MultiLevelTenant struct {
	Tenant // embedded (which itself embeds BaseResponse)
	Phone  string `json:"phone" bson:"phone"`
}

// Create inserts a Tenant — the struct_type pass should resolve
// all fields including those from embedded BaseResponse.
func Create(ctx context.Context, t *Tenant) {
	_ = t
	_ = bson.M{"name": t.Name}
}
