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
| **Edge** | OPNsense, VLAN segmentation, hard-walled DMZ, Suricata IDS, CrowdSec bouncers |
| **Remote access** | Mesh VPN only (Tailscale, moving to self-hosted NetBird). No apps published to the internet |
| **Platform** | TrueNAS SCALE, ZFS (RAIDZ2 + SSD mirror, native encryption), Docker Compose apps kept in Git |
| **Ingress and identity** | Traefik, Authentik (SSO / OIDC in front of everything), Vaultwarden |
| **Observability** | Prometheus, Alertmanager, Grafana, Loki + Alloy, Uptime Kuma, ntfy |
| **Security** | CrowdSec, Suricata, Wazuh, OpenBao 🚧, UPS-managed graceful shutdown with NUT |
| **Virtualisation** | Proxmox VE for isolated DMZ workloads |
| **Kubernetes** | Talos Linux, Cilium, Flux, cert-manager, External Secrets, Renovate, Trivy. In use, with more services still to move over from the platform box |
| **Backups** | ZFS snapshots, raw encrypted replication to a second machine, 3-2-1 with an offsite copy |
| **Self-hosted** | Forgejo, Nextcloud, Immich, Jellyfin, Navidrome, BookStack, Home Assistant 📋 |
| **Local AI** | Ollama, LiteLLM gateway, a GPU workstation for inference |

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
