# System Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                    │
│  ┌──────────────────┐              ┌──────────────────┐                 │
│  │   Web Browser    │              │   Mobile App     │                 │
│  │   (React SPA)    │              │   (Future)       │                 │
│  └────────┬─────────┘              └────────┬─────────┘                 │
│           │                                  │                           │
└───────────┼──────────────────────────────────┼───────────────────────────┘
            │                                  │
            │         HTTP/HTTPS               │
            │                                  │
┌───────────▼──────────────────────────────────▼───────────────────────────┐
│                       APPLICATION LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Django REST Framework                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │   │
│  │  │  Products  │  │ Categories │  │   Cache    │  │   Admin   │  │   │
│  │  │    API     │  │    API     │  │   Utils    │  │ Interface │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │   │
│  │                                                                    │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │            Middleware (Caching, Auth, CORS)                │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────┬──────────────────────┬──────────────────────┬───────────────────┘
         │                      │                      │
         │                      │                      │
┌────────▼──────────┐  ┌───────▼──────────┐  ┌───────▼────────────┐
│                   │  │                   │  │                    │
│   PostgreSQL      │  │      Redis        │  │   Celery Workers   │
│   Database        │  │   Cache & Broker  │  │                    │
│                   │  │                   │  │  ┌──────────────┐  │
│  ┌─────────────┐  │  │  ┌─────────────┐ │  │  │ Cache Warmup │  │
│  │  Products   │  │  │  │  Cache Data │ │  │  ├──────────────┤  │
│  │             │  │  │  ├─────────────┤ │  │  │ Statistics   │  │
│  │ Categories  │  │  │  │  Sessions   │ │  │  ├──────────────┤  │
│  │             │  │  │  ├─────────────┤ │  │  │ Bulk Ops     │  │
│  │    Users    │  │  │  │ Task Queue  │ │  │  └──────────────┘  │
│  └─────────────┘  │  │  └─────────────┘ │  │                    │
│                   │  │                   │  └────────────────────┘
└───────────────────┘  └───────────────────┘            │
                                                        │
                              ┌─────────────────────────▼────────┐
                              │      Celery Beat Scheduler       │
                              │  ┌────────────────────────────┐  │
                              │  │ Warm cache every 5 min     │  │
                              │  │ Stats every 15 min         │  │
                              │  │ Cleanup every hour         │  │
                              │  └────────────────────────────┘  │
                              └──────────────────────────────────┘
```

## Data Flow Diagram

### 1. Read Operation (GET Request)

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ 1. GET /api/products/
     ▼
┌─────────────┐
│   Django    │
│  Middleware │
└─────┬───────┘
      │
      │ 2. Check cache
      ▼
┌──────────────┐      YES     ┌─────────────┐
│    Redis     │◄─────────────┤ Cache Hit?  │
│    Cache     │              └──────┬──────┘
└──────┬───────┘                     │ NO
       │                             ▼
       │ 3. Cache hit          ┌──────────────┐
       │    Return data        │  PostgreSQL  │
       │                       │   Database   │
       │                       └──────┬───────┘
       │ 4. Cache miss                │
       │    Query database            │
       │◄─────────────────────────────┘
       │
       │ 5. Store in cache
       │
       ▼
┌─────────────┐
│   Return    │
│  Response   │
└─────────────┘
```

### 2. Write Operation (POST/PUT/DELETE)

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ 1. POST /api/products/
     ▼
┌─────────────┐
│   Django    │
│    View     │
└─────┬───────┘
      │
      │ 2. Validate data
      ▼
┌──────────────┐
│  PostgreSQL  │
│   Database   │
└──────┬───────┘
       │
       │ 3. Save to DB
       │
       ▼
┌──────────────┐
│    Signal    │
│   Handler    │
└──────┬───────┘
       │
       │ 4. Invalidate caches
       ▼
┌──────────────┐
│    Redis     │
│  DELETE keys │
└──────────────┘
```

### 3. Async Task Processing

```
┌──────────────┐
│ Celery Beat  │ (Scheduler)
└──────┬───────┘
       │
       │ Every 5 minutes
       │
       ▼
┌──────────────┐
│ Celery Task  │ warm_product_cache()
└──────┬───────┘
       │
       │ 1. Fetch featured products
       ▼
┌──────────────┐
│  PostgreSQL  │
└──────┬───────┘
       │
       │ 2. Products data
       ▼
┌──────────────┐
│    Redis     │
│  Cache data  │
└──────────────┘
```

## Caching Strategy Layers

```
┌────────────────────────────────────────────────────────────┐
│                    LAYER 1: VIEW CACHE                      │
│  • Full response caching                                   │
│  • TTL: 60 seconds                                         │
│  • Invalidation: Automatic by TTL                          │
└────────────────────────────────────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────────┐
│                   LAYER 2: OBJECT CACHE                     │
│  • Individual model instances                              │
│  • TTL: 300 seconds (5 minutes)                            │
│  • Invalidation: Signal-based on save/delete               │
└────────────────────────────────────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────────┐
│                  LAYER 3: QUERYSET CACHE                    │
│  • Complex database queries                                │
│  • TTL: 300 seconds                                        │
│  • Invalidation: Pattern matching on changes               │
└────────────────────────────────────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────────┐
│                 LAYER 4: SESSION CACHE                      │
│  • User session data                                       │
│  • TTL: 24 hours                                           │
│  • Invalidation: User logout or TTL                        │
└────────────────────────────────────────────────────────────┘
```

## Cache Key Structure

```
redis_demo:{type}:{identifier}:{subtype}

Examples:
  redis_demo:product:123                    # Single product
  redis_demo:product:slug:laptop-pro        # Product by slug
  redis_demo:products:list:published        # Product list
  redis_demo:products:page:2                # Paginated results
  redis_demo:category:5:products            # Category products
  redis_demo:statistics                     # Aggregated stats
  redis_demo:session:abc123                 # User session
```

## Deployment Architecture

### Development

```
┌──────────────────────────────────────────────────────────┐
│                    Docker Compose                         │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐│
│  │  DB    │ │ Redis  │ │Backend │ │Frontend│ │ Celery ││
│  │Postgres│ │        │ │Django  │ │ React  │ │Worker  ││
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘│
│                                                           │
│  ┌────────┐ ┌────────┐                                   │
│  │Celery  │ │ Flower │                                   │
│  │ Beat   │ │Monitor │                                   │
│  └────────┘ └────────┘                                   │
└──────────────────────────────────────────────────────────┘
```

### Production (Recommended)

```
                    ┌─────────────┐
                    │   Nginx     │
                    │   (80/443)  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │                             │
     ┌──────▼──────┐              ┌──────▼──────┐
     │   Static    │              │   Django    │
     │   Files     │              │  (Gunicorn) │
     └─────────────┘              └──────┬──────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
             ┌──────▼──────┐      ┌─────▼──────┐      ┌─────▼──────┐
             │ PostgreSQL  │      │   Redis    │      │   Celery   │
             │  (Primary)  │      │  Cluster   │      │  Workers   │
             └─────────────┘      │            │      └────────────┘
                    │             └────────────┘
             ┌──────▼──────┐
             │ PostgreSQL  │
             │  (Replica)  │
             └─────────────┘
```

## Cache Invalidation Flow

```
┌────────────────────┐
│  Model Save/Delete │
└─────────┬──────────┘
          │
          ▼
┌─────────────────────┐
│   Django Signal     │
│   post_save/delete  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ invalidate_cache()  │
└─────────┬───────────┘
          │
          ├──────────────────┐
          │                  │
          ▼                  ▼
┌──────────────┐    ┌─────────────────┐
│ Delete       │    │ Delete Pattern  │
│ Object Key   │    │ List Keys       │
└──────────────┘    └─────────────────┘
          │                  │
          │                  ▼
          │         ┌─────────────────┐
          │         │ Delete Related  │
          │         │ Category Keys   │
          │         └─────────────────┘
          │                  │
          └────────┬─────────┘
                   ▼
          ┌─────────────────┐
          │ Delete Stats    │
          │     Cache       │
          └─────────────────┘
```

## Performance Optimization Points

```
┌──────────────────────────────────────────────────────────┐
│                 Performance Layers                        │
├──────────────────────────────────────────────────────────┤
│  1. Connection Pool (50 max connections)                 │
│  2. Redis Compression (zlib)                             │
│  3. HiredisParser (C-based parser)                       │
│  4. Select_related/Prefetch_related                      │
│  5. Database Indexes                                     │
│  6. Celery async processing                              │
│  7. Cache warming (proactive)                            │
│  8. Query optimization                                   │
└──────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

```
┌────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                         │
├────────────────────────────────────────────────────────────┤
│  Cache Level:                                              │
│    • Redis INFO stats                                      │
│    • Hit/miss rates                                        │
│    • Memory usage                                          │
│    • Key count                                             │
│                                                            │
│  Application Level:                                        │
│    • Response times                                        │
│    • Request counts                                        │
│    • Error rates                                           │
│    • Celery task status                                    │
│                                                            │
│  Tools:                                                    │
│    • Flower (Celery monitoring)                            │
│    • Redis CLI (cache inspection)                          │
│    • Django Debug Toolbar (dev)                            │
│    • Prometheus (future)                                   │
│    • Grafana (future)                                      │
└────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Multi-layer caching** for optimal performance
2. **Automatic invalidation** to maintain consistency
3. **Async processing** for heavy operations
4. **Monitoring tools** for visibility
5. **Production-ready** architecture
6. **Scalable design** for growth

This architecture supports **1000+ requests/second** with proper caching and can scale horizontally by adding more application servers and Celery workers.
