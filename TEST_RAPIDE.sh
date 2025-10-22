#!/bin/bash

echo "🧪 TESTS RAPIDES 1BIP"
echo "===================="
echo ""

echo "Test 1: CompreFace UI (port 8000)"
curl -I -s http://localhost:8000 | head -1
echo ""

echo "Test 2: Dashboard (port 5000)"
curl -I -s http://localhost:5000 | head -1
echo ""

echo "Test 3: Healthcheck compreface-core (interne)"
docker-compose exec -T compreface-core curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3000/healthcheck 2>/dev/null || echo "❌ FAILED - Service non démarré"
echo ""

echo "Test 4: Processus Python dans compreface-core"
docker-compose exec -T compreface-core pgrep -l python || echo "❌ Aucun processus Python trouvé!"
echo ""

echo "Test 5: Mémoire disponible dans compreface-core"
docker-compose exec -T compreface-core free -h
echo ""

echo "✅ Tests terminés"
