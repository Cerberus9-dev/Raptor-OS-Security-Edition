# Raptor OS - Security Edition

Raptor OS Security Edition is a specialized, privacy-first Linux distribution built on Debian 12 (Bookworm). Designed for cybersecurity professionals, network analysts, and privacy advocates, it combines an arsenal of enterprise-grade auditing tools with a dynamic, hardware-level system hardening architecture. 

## Core Features

*   **Raptor Security Engine:** Dynamically switch your operational posture between three strict firewall profiles (Secure, Hardened, Lockdown) without restarting network daemons.
*   **Emergency Killswitch:** Instantly cut all physical and virtual network interfaces at the hardware level with a single command or click to prevent data leaks.
*   **Curated Security Toolkit:** Pre-configured environments for reconnaissance, digital forensics, reverse engineering, web security, and network analysis.
*   **Control Center GUI:** A native desktop dashboard providing one-click control over your security modes, firewall behavior, and emergency network state.

---

## System Requirements

### Minimum Requirements
*   **Processor:** 2.0 GHz Dual-Core 64-bit CPU
*   **Memory:** 4 GB RAM
*   **Storage:** 25 GB of free drive space (Solid State Drive highly recommended)
*   **Display:** 1024 x 768 screen resolution
*   **Network:** Standard Ethernet or Wi-Fi adapter for updates

### Recommended Specifications
*   **Processor:** 2.5 GHz Quad-Core 64-bit CPU or better
*   **Memory:** 8 GB RAM or higher (Ideal for running virtual machines or heavy network analysis)
*   **Storage:** 50 GB NVMe or SSD space
*   **Graphics:** Dedicated GPU with 3D acceleration (Beneficial for password auditing/hash cracking)

---

## Getting Started

### Live Boot vs. Installation
Raptor OS Security Edition can be run entirely from a USB drive as a Live OS, ensuring no trace is left on the host machine. Alternatively, you can use the built-in Calamares graphical installer to permanently install the OS to your hard drive.

### Managing Security Postures
Once booted, you can manage your system's exposure using the Raptor Control Center, or via the terminal:
*   `sudo raptor-security secure` (Standard outbound access, inbound dropped)
*   `sudo raptor-security hardened` (Strict egress filtering, only ports 80/443/53 allowed)
*   `sudo raptor-security lockdown` (All external traffic cut, loopback only)

To immediately terminate all connections in an emergency:
*   `sudo raptor-killswitch on`
