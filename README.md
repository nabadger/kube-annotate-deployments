# Overview

Watch for Kubernetes Deployments and send an annotation to Grafana.

## Usage

```
pipenv install
pipenv run main.py --config <path-to-config.yml>
```

## Configuration

See `./config.example.yml`

```yaml
---
grafana_token: "{GRAFANA_TOKEN}"
grafana_url: "{GRAFANA_URL}"
```

You can either specify the values in the configuration file directly, or use
Pythons format string.

In this example, `{GRAFANA_TOKEN}` and `{GRAFANA_URL}` will be looked up from the environment.

## Annotations

This application sends `POST` to the grafana `/api/annotations` URL.

It sends the following information:

- A list of annotations in the deployment
- A list of containers in the deployment
- A `kube-deployment` tag


## TODO 

- Add enable/disable annotation
- Add a makefile/dockerfile
- Some tests would be nice
