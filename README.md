# ExternalStorageSync

This was originally designed to meet a real client request for creating local copies of every file updated to that client's AWS S3 via another web application, which in turn, would send a POST request to this API in order to enqueue and the download amd storage of said file.

# Considerations
Initially, I considered using [DjangoRestFramework](https://www.django-rest-framework.org/) for this project, but given the simplicity approach required by the client, I decided to use only regular Django views with a couple of middlewares to enforce the authentication(when required) and the request payload validation.

Also, for the sake of feasibility, I replaced the AWS S3 file download logic with a dummy "NASA's Curiosity Rover image" download for each Sync request sent to the POST endpoint, that way we can test this app without setting actual AWS accounts and risk exposing credentials etc.

I added some `DISCLAIMER:` notes on the pieced of code affected by that change.

# Build
1. Save the `.env` file sent via email with the link for this repository at the root level of the project
2. If you're running on an AppleSilicon chip(M1+), please run this for architecture compatibility: `export DOCKER_DEFAULT_PLATFORM=linux/arm64`, otherwise just skip to next step.
3. Run the `build.sh` which is also at the root level:
```bash
sh ./build.sh
```
4. The app should be up and running by now, you can check that with:
```bash
curl --fail -L http://localhost:27000/sync/
```
5. You should get a response like this:
```JSON
{"synced_objects_count": 11, "queued_objects_count": 0}
```
6. You can also check the Django admin at http://localhost:27000/admin/ with the following credentials:
   * user: root
   * passowrd: admin

# Sending requests
We use the request payload HMAC checksum to both prevent unauthorized access and duplicate requests, therefore each request sent to the API needs to have a unique combination of:
  - payload request
  - matching HMAC checksum in the Authorization header

For convenience, I'm sending a txt file with sample requests that will meet those requirements and expedite the practical tests of the API, but you can generate your own tests too with `SECRET_KEY` located in the `.env` file I sent via email.

After sending some requests, go to the admin and check the results at http://localhost:27000/admin/sync/filesync/, you should be able to preview the sample NASA image downloaded like this:
![Admin Example](https://github.com/feliphebueno/external-storage-sync/assets/6662338/2a74faea-5d02-4df4-8612-04d814c208da)

# Tests and coverage
1. First of all, we need to install the dev dependencies:
```bash
docker-compose exec django-external-storage-sync pip install -r requirements/dev.txt
```
2. And then, we run the tests and coverage report with:
```bash
docker-compose exec django-external-storage-sync ./bin/integration-tests.sh
```
3. You should see an output similar to this:
![Test coverage example](https://github.com/feliphebueno/external-storage-sync/assets/6662338/53601585-7f51-4dbe-b296-d5b0d2969924)

# Stack
 - Python 3.12.2(LTS)
 - Django 4.2(LTS)
 - Postgres 16
 - Memcahed 1.6.27
 - RabbitMQ 3
 - NGINX latest
 - [Ruff](https://docs.astral.sh/) - linting/formatting
 - [Pytest](https://docs.pytest.org/) - Parallelized test runner(with xdist)
 - [Pytest Cov](https://pytest-cov.readthedocs.io/en/latest/) - Code coverage report


--- 

The app contains 2 endpoints: a GET and POST at the same path `/sync/` and their specifications are as follows:

> POST /sync/

Headers: 
```
Content-Type: application/json
Authorization: HMAC(request_payload)  # more on that below
```

Request payload:
```json
{
    "oeid": "8cfb655249106cf47fb493681d82ea",
    "ref_id": "6345307552152520612",
    "file_name": "6367458640aecc61b9736d45538952.jpg",
    "file_type": "image/jpeg"
}
```

The authentication is based on HMAC Signature of the request payload along with a SECRET_KEY shared only between the running instance of this project and the client's web application at AWS.

Request example:
```bash
curl -X POST http://localhost:27000/sync/ \
    -H "Content-Type: application/json" \
    -H "Authorization: b2234f3de1d65d9e6e87a533da87ebcdee47f2116bb93f887f647fdd70527d78" \
    -d '{"oeid": "8cfb655249106cf47fb493681d82ea", "ref_id": "6345307552152520612", "file_name": "65d9e6e87a533da87ebcdee4.jpg", "file_type": "image/jpeg"}'
```
Response:
> Status: 201 Created
```json
{
    "detail": "Object queued for sync"
}
```

Other responses are:
 - 401 - Missing/Invalid HMAC Signature
 - 400 - Mal-formed/Invalid JSON
 - 409 - Object already enqueued/synced
 - 412 - Too many requests / Request rate limit exceed

> GET /sync/

```bash
curl -X GET http://localhost:27000/sync/
```

Resposta:
> Status: 200 OK
```json
{
  "synced_objects_count": 2,
  "queued_objects_count": 1
}
```

Basic stats endpoint, should be consumed by the client's web application to keep track of the number of files already synced into the local storage and health of the app to trigger warnings in case `queued_objects_count` increases above a certain threshold.

# Available services and ports
| Service                             | Port  | Name                                   | 
|-------------------------------------|-------|----------------------------------------|
| ExternalStorageSync(nginx)          | 27000 | nginx-external-storage-sync            |
| PostgreSQL Server                   | 27001 | postgres-external-storage-sync         |
| RabbitMQ Server                     | 27002 | rabbitmq-external-storage-sync         |
| ExternalStorageSync(Djngo/Gunicorn) | 27003 | django-external-storage-sync           |

