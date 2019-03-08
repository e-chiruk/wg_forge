# WG Forge (Backend)
**Python + Flask + nginx**

### Требования

- docker

### Развертывание приложения

```sh
$ docker-compose up
```

### 1-е задание

```sh
$ curl -X GET http://localhost:8080/get_cat_colors_info
```

### 2-е задание

```sh
$ curl -X GET http://localhost:8080/get_cats_stat
```

### 3-е задание

```sh
$ curl -X GET http://localhost:8080/ping
```

### 4-е задание

```sh
$ curl -X GET http://localhost:8080/cats
$ curl -X GET http://localhost:8080/cats?attribute=name&order=asc
$ curl -X GET http://localhost:8080/cats?offset=10&limit=10
$ curl -X GET http://localhost:8080/cats?attribute=color&order=asc&offset=5&limit=2
```

### 5-е задание

```sh
$ curl -X POST http://localhost:8080/cat -H "Content-Type: application/json" -d '{"name":"Florin","color":"red & white","tail_length":15,"whiskers_length":12}'
```