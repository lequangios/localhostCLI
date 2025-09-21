# 🛠️ MAMP Project Host Manager (MPHM)

A CLI tool that helps you **create, manage, and delete Virtual Hosts in MAMP** for popular web project types like:

- 🌐 WordPress
- 🔧 Laravel
- 🐘 Plain PHP
- 📄 Static HTML

> 👤 Supports macOS and MAMP (Apache, port 8888)

---

## 🚀 Features

- ✅ Create new VirtualHost with `.yen` domain
- 🗂️ Automatically detect project type based on folder structure
- 🔁 Automatically add domain to `/etc/hosts`
- 📂 Choose custom folder for each project
- 📊 List all registered `.yen` sites
- 🗑️ Easily delete any VirtualHost
- 🌐 Open browser after setup
- 🧪 Create sample WordPress/Laravel projects
- 🔐 Simple terminal-based management, no GUI needed

---

## 🧠 Project Type Detection

| Project Type | Detection Criteria                                 |
| ------------ | -------------------------------------------------- |
| WordPress    | Contains `wp-config.php` file                      |
| Laravel      | Contains `artisan` file                            |
| Plain PHP    | Contains `.php` files but not WP or Laravel        |
| Static HTML  | Contains `.html` files, no `.php` or `artisan`     |

---

## 📦 Default Configuration

- MAMP VirtualHost config:  
  `/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf`

- Apache restart command:  
  `/Applications/MAMP/bin/apache2/bin/apachectl -k restart`

- Default port: `8888`

---

## 📋 CLI Menu

```bash
=========== MAMP HOST TOOL (.yen) ===========
1) Create new site
2) Delete site
3) List existing sites
4) Create sample WordPress/Laravel project
0) Exit
=============================================
```

---

## 🔧 System Requirements

- macOS
- MAMP installed in `/Applications/MAMP`
- Python 3
- `composer` (for Laravel)
- `curl`, `unzip` (for WordPress)
- `sudo` access to modify `/etc/hosts`

---

## 🔧 Build to Executable (Standalone)

This project includes a **stable, standalone build** process that does **not** depend on your Python env.

### 🚀 Quick Setup (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```
This will build and install MPHM globally so you can run `mphm` from anywhere.

### 🧰 Manual Build & Install
```bash
# Build only
chmod +x build.sh
./build.sh

# Install globally
chmod +x install.sh
./install.sh
```

### 🗑️ Uninstall
```bash
./uninstall.sh
```

> The build script spins up a temporary virtual environment only for building, embeds dependencies via PyInstaller, and cleans everything afterward—so the final binary runs independently of your local Python setup.

---

## 🛡️ Notes

- Always verify the selected folder matches the intended project type
- `.yen` domains only work locally if correctly added to `/etc/hosts`

---

## 🛠️ Future Plans

- Auto-create databases per site
- Support local SSL (https)
- Colorful CLI interface (using `rich`)
- Optional Docker support

---

## 👨‍💻 Author

Author: levietquangt2@gmail.com  
Experience: 10+ years in PHP/WordPress/Laravel development