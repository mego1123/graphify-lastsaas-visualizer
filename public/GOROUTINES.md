# Goroutine Leak Audit

_Target: `/home/z/my-project/repos/lastsaas/backend`_  
**Summary:** 21 goroutine launches — SAFE: 18 | RISKY: 2 | DANGEROUS: 1

## Classification key

- SAFE — goroutine has a `<-ctx.Done()` channel, a WaitGroup, or a `context.WithTimeout`/`WithDeadline` so it can be torn down.
- RISKY — no context, no WaitGroup, no timeout. May run forever; but at least has `defer recover()` so a panic won't kill the process.
- DANGEROUS — no context, no WaitGroup, no timeout, **and** no panic recovery. Highest leak / crash risk.

## DANGEROUS (1)

### `cmd/server/main.go:820` — HTTP server ListenAndServe (shutdown via http.Server.Shutdown)

- **Enclosing function:** `main`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		slog.Info("Server listening", "addr", addr) 		if err := srv.Listen`
- **Risk level:** **DANGEROUS**
- **Signals detected:** (none detected)
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		slog.Info("Server listening", "addr", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("Server failed", "error", err)
			os.Exit(1)
		}
```

</details>

## RISKY (2)

### `internal/webhooks/dispatcher.go:100` — Webhook dispatch / delivery

- **Enclosing function:** `retryWorker`
- **Launch kind:** `func_literal`
- **Launch text:** `go func(j retryJob) { 				defer func() { <-sem }() 				defer func() { 					if r`
- **Risk level:** **RISKY**
- **Signals detected:** context, recover
  - uses context.Context but no ctx.Done() receive or WithTimeout — context may not actually cancel the goroutine

<details><summary>Goroutine body preview</summary>

```go
				defer func() { <-sem }()
				defer func() {
					if r := recover(); r != nil {
						slog.Error("webhooks: dispatch panic", "panic", r, "webhook", j.hook.Name)
					}
				}()
				d.deliverWithRetry(context.Background(), j.hook, j.eventType, j.event, j.retry)
```

</details>

### `internal/webhooks/dispatcher.go:123` — Webhook dispatch / delivery

- **Enclosing function:** `Emit`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 			defer func() { <-d.emitSem }() 			defer func() { 				if r := reco`
- **Risk level:** **RISKY**
- **Signals detected:** recover

<details><summary>Goroutine body preview</summary>

```go
			defer func() { <-d.emitSem }()
			defer func() {
				if r := recover(); r != nil {
					slog.Error("webhooks: emit panic", "panic", r, "event_type", eventType)
				}
			}()
			d.dispatch(eventType, event)
```

</details>

## SAFE (18)

### `internal/api/handlers/admin.go:1753` — Send invitation email in the background

- **Enclosing function:** `InviteRootMember`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		ctx, cancel := context.WithTimeout(context.Background(), 30*time.S`
- **Risk level:** **SAFE**
- **Signals detected:** context, timeout
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		_ = ctx
		if h.emailService != nil {
			if err := h.emailService.SendInvitationEmail(req.Email, user.DisplayName, rootTenant.Name, token); err != nil {
				slog.Error("Failed to send root member invitation email", "to", req.Email, "error", err)
			}
		}
```

</details>

### `internal/api/handlers/auth.go:698` — Send password-reset email in the background

- **Enclosing function:** `ForgotPassword`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		ctx, cancel := context.WithTimeout(context.Background(), 30*time.S`
- **Risk level:** **SAFE**
- **Signals detected:** context, timeout
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		_ = ctx
		if h.emailService != nil {
			if err := h.emailService.SendPasswordResetEmail(user.Email, user.DisplayName, resetToken); err != nil {
				slog.Error("Failed to send password reset email", "error", err)
			}
		}
```

</details>

### `internal/api/handlers/auth.go:1188` — Send magic-link email in the background

- **Enclosing function:** `MagicLinkRequest`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		ctx, cancel := context.WithTimeout(context.Background(), 30*time.S`
- **Risk level:** **SAFE**
- **Signals detected:** context, timeout
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		_ = ctx
		if h.emailService != nil {
			if err := h.emailService.SendMagicLinkEmail(user.Email, user.DisplayName, magicToken); err != nil {
				slog.Error("Failed to send magic link email", "error", err)
			}
		}
```

</details>

### `internal/api/handlers/auth.go:2009` — Send verification email in the background

- **Enclosing function:** `sendVerificationEmail`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		ctx, cancel := context.WithTimeout(context.Background(), 30*time.S`
- **Risk level:** **SAFE**
- **Signals detected:** context, timeout
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		_ = ctx
		if h.emailService != nil {
			if err := h.emailService.SendVerificationEmail(userEmail, displayName, verificationToken); err != nil {
				slog.Error("Failed to send verification email", "to", userEmail, "error", err)
			}
		} else {
			slog.Warn("Email service not configured, logging verification token", "email", userEmail, "token", verificationToken)
		}
```

</details>

### `internal/api/handlers/tenant.go:262` — Send invitation email in the background

- **Enclosing function:** `InviteMember`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		ctx, cancel := context.WithTimeout(context.Background(), 30*time.S`
- **Risk level:** **SAFE**
- **Signals detected:** context, timeout
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		_ = ctx
		if h.emailService != nil {
			if err := h.emailService.SendInvitationEmail(req.Email, user.DisplayName, tenant.Name, token); err != nil {
				slog.Error("Failed to send invitation email", "to", req.Email, "error", err)
			}
		}
```

</details>

### `internal/configstore/store.go:120` — Background config auto-reload

- **Enclosing function:** `StartAutoReload`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		ticker := time.NewTicker(interval) 		defer ticker.Stop() 		for {`
- **Risk level:** **SAFE**
- **Signals detected:** done-channel, waitgroup
  - wg.Done() in body but no nearby wg.Add() — check caller adds to WaitGroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				if err := s.Load(ctx); err != nil {
					slog.Warn("configstore: auto-reload failed", "error", err)
				}
			}
		}
```

</details>

### `internal/datadog/client.go:119` — DataDog metrics flush loop

- **Enclosing function:** `New`
- **Launch kind:** `func_call`
- **Launch text:** `go c.metricsFlushLoop() 	go c.eventsFlushLoop() 	go c.logsFlushLoop() 	go c.chec`
- **Risk level:** **SAFE**
- **Signals detected:** done-channel, waitgroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
	defer c.wg.Done()
	backoff := flushInterval
	timer := time.NewTimer(backoff)
	timer.Stop()
	buf := make([]metricPoint, 0, metricsBufferSize)
	flush := func() bool {
		if len(buf) == 0 {
			return true
		}
		if err := c.submitMetrics(buf); err != nil {
			slog.Warn("datadog: metrics flush failed, will retry", "count", len(buf), "error", err)
			return false
```

</details>

### `internal/datadog/client.go:120` — DataDog events flush loop

- **Enclosing function:** `New`
- **Launch kind:** `func_call`
- **Launch text:** `go c.eventsFlushLoop() 	go c.logsFlushLoop() 	go c.checksFlushLoop() 	return c }`
- **Risk level:** **SAFE**
- **Signals detected:** done-channel, waitgroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
	defer c.wg.Done()
	for {
		select {
		case evt := <-c.eventsCh:
			if err := c.submitEvent(evt); err != nil {
				slog.Warn("datadog: event submission failed", "title", evt.Title, "error", err)
			}
		case <-c.stopCh:
			for {
				select {
				case evt := <-c.eventsCh:
					if err := c.submitEvent(evt); err != nil {
```

</details>

### `internal/datadog/client.go:121` — DataDog logs flush loop

- **Enclosing function:** `New`
- **Launch kind:** `func_call`
- **Launch text:** `go c.logsFlushLoop() 	go c.checksFlushLoop() 	return c }    func resolveHostname`
- **Risk level:** **SAFE**
- **Signals detected:** done-channel, waitgroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
	defer c.wg.Done()
	backoff := logsFlushInterval
	timer := time.NewTimer(backoff)
	timer.Stop()
	buf := make([]ddLog, 0, logsBufferSize)
	flush := func() bool {
		if len(buf) == 0 {
			return true
		}
		if err := c.submitLogs(buf); err != nil {
			slog.Warn("datadog: logs flush failed, will retry", "count", len(buf), "error", err)
			return false
```

</details>

### `internal/datadog/client.go:122` — DataDog service-check flush loop

- **Enclosing function:** `New`
- **Launch kind:** `func_call`
- **Launch text:** `go c.checksFlushLoop() 	return c }    func resolveHostname(configHostname string`
- **Risk level:** **SAFE**
- **Signals detected:** done-channel, waitgroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
	defer c.wg.Done()
	for {
		select {
		case check := <-c.checksCh:
			if err := c.submitServiceCheck(check); err != nil {
				slog.Warn("datadog: service check submission failed", "check", check.Check, "error", err)
			}
		case <-c.stopCh:
			for {
				select {
				case check := <-c.checksCh:
					if err := c.submitServiceCheck(check); err != nil {
```

</details>

### `internal/health/health.go:65` — Health heartbeat loop

- **Enclosing function:** `Start`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		defer s.wg.Done() 		s.heartbeatLoop() 	}() 	go func() { 		defer s.`
- **Risk level:** **SAFE**
- **Signals detected:** waitgroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		defer s.wg.Done()
		s.heartbeatLoop()
```

</details>

### `internal/health/health.go:69` — Metrics collector loop

- **Enclosing function:** `Start`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		defer s.wg.Done() 		s.collectorLoop() 	}() 	go func() { 		defer s.`
- **Risk level:** **SAFE**
- **Signals detected:** waitgroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		defer s.wg.Done()
		s.collectorLoop()
```

</details>

### `internal/health/health.go:73` — Integration-check loop

- **Enclosing function:** `Start`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		defer s.wg.Done() 		s.integrationCheckLoop() 	}() 	slog.Info("Heal`
- **Risk level:** **SAFE**
- **Signals detected:** waitgroup
  - wg.Done() in body but no nearby wg.Add() — check caller adds to WaitGroup
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		defer s.wg.Done()
		s.integrationCheckLoop()
```

</details>

### `internal/metrics/metrics.go:43` — Periodic ticker-driven background task

- **Enclosing function:** `Start`
- **Launch kind:** `func_call`
- **Launch text:** `go s.run() 	slog.Info("Daily metrics service started", "holder", s.holderID) }`
- **Risk level:** **SAFE**
- **Signals detected:** done-channel
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
	if s.tryAcquireOrRenew() {
		s.collectDaily()
	}
	renewTicker := time.NewTicker(renewalTick)
	collectTicker := time.NewTicker(collectTick)
	defer renewTicker.Stop()
	defer collectTicker.Stop()
	for {
		select {
		case <-renewTicker.C:
			s.tryAcquireOrRenew()
		case <-collectTicker.C:
```

</details>

### `internal/middleware/auth.go:151` — Asynchronous DB update

- **Enclosing function:** `authenticateAPIKey`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Se`
- **Risk level:** **SAFE**
- **Signals detected:** context, timeout
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		now := time.Now()
		_, _ = m.db.APIKeys().UpdateByID(ctx, apiKey.ID,
			bson.M{"$set": bson.M{"lastUsedAt": now}})
```

</details>

### `internal/middleware/ratelimit.go:77` — Periodic cleanup of expired entries

- **Enclosing function:** `NewRateLimiter`
- **Launch kind:** `func_literal`
- **Launch text:** `go func() { 		for { 			select { 			case <-rl.cleanup.C: 				rl.cleanupExpired()`
- **Risk level:** **SAFE**
- **Signals detected:** done-channel
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
		for {
			select {
			case <-rl.cleanup.C:
				rl.cleanupExpired()
			case <-rl.done:
				return
			}
		}
```

</details>

### `internal/telemetry/service.go:58` — Telemetry flush loop

- **Enclosing function:** `New`
- **Launch kind:** `func_call`
- **Launch text:** `go s.flushLoop() 	return s }   func (s *Service) Stop() { 	close(s.stopCh) 	<-s.`
- **Risk level:** **SAFE**
- **Signals detected:** context, done-channel, timeout
  - no defer recover() — a panic will crash the process

<details><summary>Goroutine body preview</summary>

```go
	defer close(s.stopped)
	backoff := trackFlushInterval
	timer := time.NewTimer(backoff)
	timer.Stop()
	buf := make([]interface{}, 0, trackBufferSize)
	flush := func() bool {
		if len(buf) == 0 {
			return true
		}
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		_, err := s.db.TelemetryEvents().InsertMany(ctx, buf)
		cancel()
```

</details>

### `internal/webhooks/dispatcher.go:59` — Webhook retry worker loop

- **Enclosing function:** `NewDispatcher`
- **Launch kind:** `func_call`
- **Launch text:** `go d.retryWorker() 	return d }   func (d *Dispatcher) EncryptionKey() []byte {`
- **Risk level:** **SAFE**
- **Signals detected:** context, done-channel, recover

<details><summary>Goroutine body preview</summary>

```go
	defer close(d.stopped)
	sem := make(chan struct{}, maxRetryWorkers)
	for {
		select {
		case <-d.stopCh:
			return
		case job := <-d.retryQ:
			delay := time.Until(job.fireAt)
			if delay > 0 {
				timer := time.NewTimer(delay)
				select {
				case <-timer.C:
```

</details>

## All findings (table)

| File | Line | Function | Purpose | Risk | Signals |
|------|------|----------|---------|------|---------|
| cmd/server/main.go | 820 | main | HTTP server ListenAndServe (shutdown via http.Server.Shutdow | DANGEROUS | — |
| internal/webhooks/dispatcher.go | 100 | retryWorker | Webhook dispatch / delivery | RISKY | context, recover |
| internal/webhooks/dispatcher.go | 123 | Emit | Webhook dispatch / delivery | RISKY | recover |
| internal/api/handlers/admin.go | 1753 | InviteRootMember | Send invitation email in the background | SAFE | context, timeout |
| internal/api/handlers/auth.go | 698 | ForgotPassword | Send password-reset email in the background | SAFE | context, timeout |
| internal/api/handlers/auth.go | 1188 | MagicLinkRequest | Send magic-link email in the background | SAFE | context, timeout |
| internal/api/handlers/auth.go | 2009 | sendVerificationEmail | Send verification email in the background | SAFE | context, timeout |
| internal/api/handlers/tenant.go | 262 | InviteMember | Send invitation email in the background | SAFE | context, timeout |
| internal/configstore/store.go | 120 | StartAutoReload | Background config auto-reload | SAFE | done-channel, waitgroup |
| internal/datadog/client.go | 119 | New | DataDog metrics flush loop | SAFE | done-channel, waitgroup |
| internal/datadog/client.go | 120 | New | DataDog events flush loop | SAFE | done-channel, waitgroup |
| internal/datadog/client.go | 121 | New | DataDog logs flush loop | SAFE | done-channel, waitgroup |
| internal/datadog/client.go | 122 | New | DataDog service-check flush loop | SAFE | done-channel, waitgroup |
| internal/health/health.go | 65 | Start | Health heartbeat loop | SAFE | waitgroup |
| internal/health/health.go | 69 | Start | Metrics collector loop | SAFE | waitgroup |
| internal/health/health.go | 73 | Start | Integration-check loop | SAFE | waitgroup |
| internal/metrics/metrics.go | 43 | Start | Periodic ticker-driven background task | SAFE | done-channel |
| internal/middleware/auth.go | 151 | authenticateAPIKey | Asynchronous DB update | SAFE | context, timeout |
| internal/middleware/ratelimit.go | 77 | NewRateLimiter | Periodic cleanup of expired entries | SAFE | done-channel |
| internal/telemetry/service.go | 58 | New | Telemetry flush loop | SAFE | context, done-channel, timeout |
| internal/webhooks/dispatcher.go | 59 | NewDispatcher | Webhook retry worker loop | SAFE | context, done-channel, recover |

## Recommendations

1. **Fix 1 DANGEROUS goroutine(s) first** — add `defer recover()` and a cancellation path (`context.WithTimeout` or a `<-done` select).
2. **Review 2 RISKY goroutine(s)** — they have `recover()` but no shutdown signal. If they perform I/O, wrap with `context.WithTimeout` so a stuck downstream call can't pin the goroutine forever.
3. For HTTP-handler fire-and-forget email sends, prefer passing a request-scoped context or a small bounded `context.WithTimeout(context.Background(), 30*time.Second)`.
4. For long-lived background loops, ensure they expose a `Stop()` method that closes a `stopCh` and that callers actually invoke it on shutdown.
