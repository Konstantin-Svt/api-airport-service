# Airport API

API service for airport managment written with the help of DRF

## Installing
  ```bash
  git clone https://github.com/Konstantin-Svt/api-airport-service.git
  cd api-airport-service
  set POSTGRES_PASSWORD=<your password for database>
  ```
  - Although you can set other enviroment variables, like ```POSTGRES_DB, POSTGRES_USER, POSTGRES_HOST, SECRET_KEY, DEBUG``` etc., a mandatory one is only ```POSTGRES_PASSWORD```. Others shall be default value if not specified. Also you can write them to your own ```.env``` file.
  - Install and run Docker.
  ```bash
  docker-compose build
  docker-compose up
  ```
  - If you want to load some sample data:
  ```bash
  docker exec -it api-airport-service-app-1 python manage.py loaddata fixtures/data.json
  ```
  - Create user at ```127.0.0.1:8000/api/user/register/``` or use default admin profile if you loaded sample data:
  ```bash
  email: admin@admin
  password: admin
  ```
  - Obtain JWT token at ```127.0.0.1:8000/api/user/token/```
  - Airport API is available at ```127.0.0.1:8000/api/airport/```

## Features
- JWT Authentication
- Admin panel ```127.0.0.1:8000/admin/```
- Documentation ```127.0.0.1:8000/api/schema/swagger```
- Managing orders and tickets
- Admins can retrieve other users orders details. Default Users can see only their own orders
- Admins can create, alter, delete flights with airplanes, routes and crew
- Admins can upload images for Airplane Types at ```127.0.0.1:8000/api/airport/airplane_types/{id}/upload-image/``` endpoint
- Filtering flights with sources and destinations (cities), and date (as departure date)
- Tickets validation (no duplications, already bought ones)
- Flights create validation (no arrival time earlier than departure time)
- Replaced Django's default User Username with Email