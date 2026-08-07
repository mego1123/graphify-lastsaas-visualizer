package duplicate_findings

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
)

// ListLogs simulates the real-world case where one function has two
// separate Find calls on the same collection with the same (empty)
// filter_fields. The dict-collision bug would collapse these into one
// finding; the test verifies both survive.
type LogHandler struct{}

func (h *LogHandler) ListLogs(ctx context.Context) {
	// First Find call — empty filter
	_ = bson.M{}
	// Second Find call — also empty filter
	// Both should appear as separate findings in the tracer output.
	_ = bson.M{}
}
