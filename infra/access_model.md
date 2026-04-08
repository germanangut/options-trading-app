# Access Model Definition and Setup Guide

This document defines a simple, controlled access model for the deployed app in its current stage.

> The app is currently intended for **private/internal usage** as a single-user or limited-user decision-support system.

## 1. Access model

### Access posture

- **Private, not public**
- Intended for controlled access by a small number of trusted internal users
- Not designed or documented here as an internet-open, multi-user application

### Intended user scope

The current expected audience is:

- the owner/operator of the system
- a small number of trusted internal reviewers, if needed

This matches the current product stage and avoids overstating readiness.

## 2. Domain or subdomain usage

Instead of exposing the app only through a raw IP and port, use a simple internal domain or subdomain, for example:

- `options.internal.example.com`
- `trading-view.company.local`

DNS should map the chosen domain/subdomain to the VM's IP address.

Example DNS concept:

```text
options.internal.example.com -> <vm-public-or-private-ip>
```

This improves usability and prepares the deployment for cleaner proxy and HTTPS handling.

## 3. Reverse proxy model with Nginx

Place **Nginx** in front of the Streamlit app and route standard web traffic from port `80` / `443` to the app running on port `8501`.

Recommended model:

- Nginx listens on `80` and later `443`
- Nginx proxies requests to `http://127.0.0.1:8501`
- Direct public exposure of `8501` should be avoided where possible

Benefits:

- cleaner access via domain name
- central place for access control
- easier future HTTPS enablement
- hides the raw Streamlit port from normal user access

## 4. Basic authentication approach

For the current stage, use **HTTP Basic Auth via Nginx**.

### Purpose

- provide a lightweight access gate for private/internal usage
- prevent casual or accidental open access to the deployed UI
- add a simple control layer without changing application code

### Limitations

- not a full identity or authorization system
- shared or static credentials are operationally simple but limited
- should be treated as an interim protection model, not a long-term product auth strategy

## 5. Example Nginx configuration snippet

```nginx
server {
    listen 80;
    server_name options.internal.example.com;

    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

This example shows the basic pattern only. Exact VM paths and Nginx site layout can vary by environment.

## 6. Future HTTPS setup

Once the domain is in place, HTTPS can be added using a standard certificate flow such as **Let's Encrypt**.

Future HTTPS expectations:

- terminate TLS at Nginx
- redirect HTTP to HTTPS
- keep the app proxied internally on port `8501`

## 7. Future authentication evolution

If the user scope expands or the app moves toward broader operational use, the access model should evolve beyond Basic Auth.

Likely future options include:

- identity-aware access via a proper internal SSO solution
- stronger user-specific authentication and session control
- more explicit authorization boundaries if usage broadens

## 8. Current recommendation summary

For the current deployment target and product stage, the recommended access model is:

1. private/internal access only
2. domain or subdomain mapped to the VM
3. Nginx reverse proxy in front of Streamlit
4. HTTP Basic Auth as a lightweight interim protection layer
5. HTTPS added next when domain management is available
