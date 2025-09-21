# 🚀 FE LAMP CLI

LAMP stack local management via Homebrew. Provides two CLIs:

- `lamp_cli.py` → binary `fe_lamp`: Install/Configure/Start/Stop LAMP (Apache, PHP, MySQL/MariaDB, phpMyAdmin)
- `lamp_site_cli.py` → binary `fe_lamp_site`: Manage local virtual hosts, domains, and project templates

No longer depends on MAMP. Everything runs on Homebrew services and standard Apache configs.

---

## ✨ Features

- Install/upgrade Apache, PHP, MySQL/MariaDB, phpMyAdmin via Homebrew
- Auto-configure Apache for PHP, phpMyAdmin aliases, PHP session dir, MySQL root (`root/fe_root`)
- Persist configuration to `/opt/fe_lamp/fe_lamp.json`
- Manage virtual hosts with JSON source `/opt/fe_lamp/fe_lamp_site.json`
- Start/stop/restart services (phpMyAdmin excluded from service ops)
- Change Apache port and document root
- Robust PHP/MySQL/phpMyAdmin tests
- Dynamic dashboard (`index.php`) auto-deployed to doc root using `template/index_template.php`

---

## 🧠 Project Type Detection (fe_lamp_site)

| Type       | Marker                                       |
| ---------- | -------------------------------------------- |
| WordPress  | `wp-config.php`                              |
| Laravel    | `artisan`                                    |
| Symfony    | `bin/console` or `symfony.lock`              |
| Drupal     | `core/lib/Drupal.php` or `web/core/...`      |
| Magento    | `bin/magento` and `app/code`                 |
| PHP        | Common PHP files in root                     |
| HTML       | `index.html` / `home.html`                   |
| JavaScript | `package.json`                               |

Parent directory is also checked to handle cases like Laravel `public/`.

---

## 🔧 Requirements

- macOS
- Homebrew
- Python 3
- `sudo` access (for Apache/httpd.conf, /etc/hosts, /opt/fe_lamp)

---

## 📦 Build Binaries

`build.sh` is now parameterized.

```bash
# fe_local (legacy example)
./build.sh

# fe_lamp
./build.sh --script lamp_cli.py --name fe_lamp

# fe_lamp_site
./build.sh --script lamp_site_cli.py --name fe_lamp_site

# force rebuild
./build.sh --script lamp_cli.py --name fe_lamp --force
```

Install globally:

```bash
# install
./install.sh --name fe_lamp
./install.sh --name fe_lamp_site

# uninstall
./uninstall.sh --name fe_lamp
./uninstall.sh --name fe_lamp_site
```

All-in-one setup (build + install):

```bash
./setup.sh --script lamp_cli.py --name fe_lamp
./setup.sh --script lamp_site_cli.py --name fe_lamp_site
```

---

## 🧭 Usage

Core LAMP management:

```bash
fe_lamp status
fe_lamp install --db mysql
fe_lamp start | stop | restart
fe_lamp configure-apache --port 8080 --doc-root /opt/homebrew/var/www
fe_lamp show-apache-config
```

Site management:

```bash
fe_lamp_site          # interactive menu
fe_lamp_site --help   # help
```

Backed by:
- Apache vhosts: `/opt/homebrew/etc/httpd/extra/httpd-vhosts.conf`
- Hosts file: `/etc/hosts`
- Config: `/opt/fe_lamp/fe_lamp.json`, `/opt/fe_lamp/fe_lamp_site.json`

---

## 📄 Dashboard

After installation, `template/index_template.php` is copied to the Apache doc root as `index.php`. The page binds data from `fe_lamp_site.json` and groups projects by type.

---

## 👨‍💻 Author

Author: levietquangt2@gmail.com  
Experience: 10+ years in PHP/WordPress/Laravel development