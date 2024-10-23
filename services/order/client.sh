# Create
for i in {1..10}; do curl -X POST http://localhost:8000/orders/ -H 'Content-Type: application/json' -d '{"email": "20a37932493f4e00b520c8e2d1f706ff@one.com"}'; done

# List
curl http://localhost:8000/orders/?email=20a37932493f4e00b520c8e2d1f706ff@one.com
