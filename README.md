# ticketmaster_weather_mini_project

# Uruchomienie
docker compose -f docker-compose.{dev/test/prod}.yml up -d --build

# Logi
docker compose -f docker-compose.{dev/test/prod}.yml logs -f backend

# Wyłączenie
docker compose -f docker-compose.{dev/test/prod}.yml down -v

# Restart backendu
docker compose -f docker-compose.{dev/test/prod}.yml restart backend