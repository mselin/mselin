<div align="center">

<img src="assets/header.svg" alt="Mika Selin: DevOps engineer and homelab builder" width="840">

<br>

[![Website](https://img.shields.io/badge/website-mselin.github.io-3ddc97?style=for-the-badge&logo=githubpages&logoColor=white&labelColor=0d1420)](https://mselin.github.io)
[![Codeberg](https://img.shields.io/badge/codeberg-mselin-5cc8ff?style=for-the-badge&logo=codeberg&logoColor=white&labelColor=0d1420)](https://codeberg.org/mselin)

</div>

## 👋 Hi

I build and run infrastructure for a living, and then go home and do it again for fun. Most of my
recent work lives in a self-hosted Forgejo, so this profile is the public window into it: how the
lab is put together, what it runs, and the bits of code that make it out into the open.

- 🔭 **Now:** running a Talos Kubernetes cluster with Flux GitOps and moving more and more workloads onto it, plus getting secrets into OpenBao
- 🔐 **Care about:** least privilege, encrypted backups that are actually restore-tested, boring reliability
- 🎛️ **Also:** retro audio. C64 SID chips, MIDI and hardware synths

## 🏠 The homelab

This is a learning environment first. A firewall splits the network into isolated segments, the DMZ
can't reach anything, and no app is exposed to the internet: everything is reached over a mesh VPN.

Right now one platform box carries storage, apps, identity and observability. That makes it a single
point of failure, and it is there because of budget, not because it is the design I would choose.
The Kubernetes cluster is the way out of it: new services land there, and existing ones move over
bit by bit.

```mermaid
flowchart LR
  inet((Internet)) --> fw[Firewall / router<br/>OPNsense · Suricata · CrowdSec]
  vpn[(Mesh VPN<br/>Tailscale → NetBird)] -. all app access .-> ingress

  fw --> sw[Segmented network<br/>mgmt · trusted · guest · IoT · DMZ]

  sw --> nas[Platform<br/>TrueNAS SCALE · ZFS]
  sw --> dns[DNS<br/>AdGuard Home ×2 · Unbound]
  sw --> dmz[DMZ hypervisor<br/>Proxmox VE]
  sw --> k8s[Kubernetes<br/>Talos · Cilium · Flux]

  nas --> ingress[Traefik + Authentik SSO]
  nas --> obs[Observability<br/>Prometheus · Grafana · Loki]
  nas --> sec[Security<br/>Wazuh · CrowdSec · OpenBao]
  nas -- encrypted ZFS replication --> bak[Backup target<br/>going offsite]
  nas -. workloads migrating .-> k8s
```

| Layer | What runs there |
|---|---|
| **Edge** | [OPNsense](https://github.com/opnsense/core), VLAN segmentation, hard-walled DMZ, [Suricata](https://github.com/OISF/suricata) IDS, [CrowdSec](https://github.com/crowdsecurity/crowdsec) bouncers |
| **Remote access** | Mesh VPN only ([Tailscale](https://github.com/tailscale/tailscale), moving to self-hosted [NetBird](https://github.com/netbirdio/netbird)). No apps published to the internet |
| **Platform** | [TrueNAS SCALE](https://github.com/truenas/middleware), ZFS (RAIDZ2 + SSD mirror, native encryption), Docker Compose apps kept in Git |
| **Ingress and identity** | [Traefik](https://github.com/traefik/traefik), [Authentik](https://github.com/goauthentik/authentik) (SSO / OIDC in front of everything) |
| **Observability** | [Prometheus](https://github.com/prometheus/prometheus), [Alertmanager](https://github.com/prometheus/alertmanager), [Grafana](https://github.com/grafana/grafana), [Loki](https://github.com/grafana/loki) + [Alloy](https://github.com/grafana/alloy), [Uptime Kuma](https://github.com/louislam/uptime-kuma), [ntfy](https://github.com/binwiederhier/ntfy) |
| **Security** | [CrowdSec](https://github.com/crowdsecurity/crowdsec), [Suricata](https://github.com/OISF/suricata), [Wazuh](https://github.com/wazuh/wazuh), [Vaultwarden](https://github.com/dani-garcia/vaultwarden), [OpenBao](https://github.com/openbao/openbao) 🚧, UPS-managed graceful shutdown with [NUT](https://github.com/networkupstools/nut) |
| **Virtualisation** | Proxmox VE for isolated DMZ workloads |
| **Kubernetes** | [Talos](https://github.com/siderolabs/talos) Linux, [Cilium](https://github.com/cilium/cilium), [Flux](https://github.com/fluxcd/flux2), [cert-manager](https://github.com/cert-manager/cert-manager), [External Secrets](https://github.com/external-secrets/external-secrets), [Renovate](https://github.com/renovatebot/renovate), [Trivy](https://github.com/aquasecurity/trivy). In use, with more services still to move over from the platform box |
| **Backups** | ZFS snapshots, raw encrypted replication to a second machine, 3-2-1 with an offsite copy |

### App stack

Everything sits behind SSO, is kept as Compose files in Git, and is grouped on a Homepage dashboard
the same way as here. Each name links to the project behind it.

| Group | Apps |
|---|---|
| **AI** | [Ollama](https://github.com/ollama/ollama), [LiteLLM](https://github.com/BerriAI/litellm) gateway, [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm), Strata (local LLM on a GPU workstation) |
| **Tools** | [Forgejo](https://codeberg.org/forgejo/forgejo), [Nextcloud](https://github.com/nextcloud/server), [BookStack](https://github.com/BookStackApp/BookStack), [Trilium Notes](https://github.com/TriliumNext/Trilium), [Joplin](https://github.com/laurent22/joplin), [Wallabag](https://github.com/wallabag/wallabag), [Karakeep](https://github.com/karakeep-app/karakeep), [Mealie](https://github.com/mealie-recipes/mealie), [Homebox](https://github.com/sysadminsmedia/homebox), [Draw.io](https://github.com/jgraph/drawio), [Code Server](https://github.com/coder/code-server), [JupyterLab](https://github.com/jupyterlab/jupyterlab), [pgAdmin](https://github.com/pgadmin-org/pgadmin4), [Syncthing](https://github.com/syncthing/syncthing), [Filebrowser](https://github.com/filebrowser/filebrowser), [Vaultwarden](https://github.com/dani-garcia/vaultwarden), [Speedtest Tracker](https://github.com/alexjustesen/speedtest-tracker), [Open Speedtest](https://github.com/openspeedtest/Speed-Test), [Domain Watchdog](https://github.com/maelgangloff/domain-watchdog) |
| **Media** | [Jellyfin](https://github.com/jellyfin/jellyfin), [Jellystat](https://github.com/CyferShepard/Jellystat), [Navidrome](https://github.com/navidrome/navidrome), [Lyrion](https://github.com/LMS-Community/slimserver), [Audiobookshelf](https://github.com/advplyr/audiobookshelf), [Kavita](https://github.com/Kareadita/Kavita), [Immich](https://github.com/immich-app/immich), [Tdarr](https://github.com/HaveAGitGat/Tdarr), [MeTube](https://github.com/alexta69/metube) |
| **Monitoring** | [Prometheus](https://github.com/prometheus/prometheus), [Alertmanager](https://github.com/prometheus/alertmanager), [Grafana](https://github.com/grafana/grafana), [Uptime Kuma](https://github.com/louislam/uptime-kuma), [ntfy](https://github.com/binwiederhier/ntfy), [Wazuh](https://github.com/wazuh/wazuh), [CrowdSec](https://github.com/crowdsecurity/crowdsec), [Portainer](https://github.com/portainer/portainer), [Traefik](https://github.com/traefik/traefik), [Authentik](https://github.com/goauthentik/authentik), [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) ×2, plus dashboards for the firewall, NAS, hypervisor, Wi-Fi controller and UPS |
| **Home automation** | [Home Assistant](https://github.com/home-assistant/core) 📋 |

<sub>🚧 in progress · 📋 planned</sub>

## 🧰 Toolbox

<p>
<img alt="Linux" src="https://img.shields.io/badge/Linux-0d1420?style=flat-square&logo=linux&logoColor=white">
<img alt="Debian" src="https://img.shields.io/badge/Debian-0d1420?style=flat-square&logo=debian&logoColor=white">
<img alt="NixOS" src="https://img.shields.io/badge/NixOS-0d1420?style=flat-square&logo=nixos&logoColor=white">
<img alt="OPNsense" src="https://img.shields.io/badge/OPNsense-0d1420?style=flat-square&logo=opnsense&logoColor=white">
<img alt="TrueNAS" src="https://img.shields.io/badge/TrueNAS-0d1420?style=flat-square&logo=truenas&logoColor=white">
<img alt="Proxmox" src="https://img.shields.io/badge/Proxmox-0d1420?style=flat-square&logo=proxmox&logoColor=white">
<img alt="Docker" src="https://img.shields.io/badge/Docker-0d1420?style=flat-square&logo=docker&logoColor=white">
<img alt="Kubernetes" src="https://img.shields.io/badge/Kubernetes-0d1420?style=flat-square&logo=kubernetes&logoColor=white">
<img alt="Talos" src="https://img.shields.io/badge/Talos-0d1420?style=flat-square&logo=talos&logoColor=white">
<img alt="Flux" src="https://img.shields.io/badge/Flux-0d1420?style=flat-square&logo=flux&logoColor=white">
<img alt="Cilium" src="https://img.shields.io/badge/Cilium-0d1420?style=flat-square&logo=cilium&logoColor=white">
<img alt="Traefik" src="https://img.shields.io/badge/Traefik-0d1420?style=flat-square&logo=traefikproxy&logoColor=white">
<img alt="Authentik" src="https://img.shields.io/badge/Authentik-0d1420?style=flat-square&logo=authentik&logoColor=white">
<img alt="Cloudflare" src="https://img.shields.io/badge/Cloudflare-0d1420?style=flat-square&logo=cloudflare&logoColor=white">
<img alt="Prometheus" src="https://img.shields.io/badge/Prometheus-0d1420?style=flat-square&logo=prometheus&logoColor=white">
<img alt="Grafana" src="https://img.shields.io/badge/Grafana-0d1420?style=flat-square&logo=grafana&logoColor=white">
<img alt="Forgejo" src="https://img.shields.io/badge/Forgejo-0d1420?style=flat-square&logo=forgejo&logoColor=white">
<img alt="Renovate" src="https://img.shields.io/badge/Renovate-0d1420?style=flat-square&logo=renovate&logoColor=white">
<img alt="Python" src="https://img.shields.io/badge/Python-0d1420?style=flat-square&logo=python&logoColor=white">
<img alt="Bash" src="https://img.shields.io/badge/Bash-0d1420?style=flat-square&logo=gnubash&logoColor=white">
<img alt="Ollama" src="https://img.shields.io/badge/Ollama-0d1420?style=flat-square&logo=ollama&logoColor=white">
</p>

## 📦 Projects

| Project | What it is |
|---|---|
| [sidplay4-asidmod](https://github.com/mselin/sidplay4-asidmod) | SIDPLAY with ASID output, for playing C64 SID tunes on real SID hardware over MIDI |
| [machine-learning-udacity](https://github.com/mselin/machine-learning-udacity) | Coursework and notebooks from Udacity's machine learning programme |
| Homelab infrastructure | Compose stacks, GitOps manifests and runbooks. Lives in self-hosted Forgejo; public pieces are on their way to [Codeberg](https://codeberg.org/mselin) |

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mselin/mselin/output/snake-dark.svg">
  <img alt="Contribution graph being eaten by a snake" src="https://raw.githubusercontent.com/mselin/mselin/output/snake.svg">
</picture>

</div>
