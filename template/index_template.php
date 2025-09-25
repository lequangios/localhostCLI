<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Four elements - Web Server</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .tabs-container {
            margin-bottom: 40px;
        }
        
        .tabs-nav {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 5px;
            backdrop-filter: blur(10px);
        }
        
        .tab-button {
            flex: 1;
            padding: 15px 20px;
            background: transparent;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .tab-button.active {
            background: rgba(255, 255, 255, 0.2);
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        
        .tab-button:hover:not(.active) {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .projects {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .project-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .project-card h3 {
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: #fff;
        }
        
        .project-card p {
            margin-bottom: 20px;
            opacity: 0.9;
            line-height: 1.6;
        }
        
        .project-links {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .project-link {
            display: inline-block;
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s ease;
            text-align: center;
            font-weight: 500;
        }
        
        .project-link:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .project-link.primary {
            background: #4CAF50;
        }
        
        .project-link.primary:hover {
            background: #45a049;
        }
        
        .project-link.secondary {
            background: #2196F3;
        }
        
        .project-link.secondary:hover {
            background: #1976D2;
        }
        
        .status {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .status h2 {
            margin-bottom: 15px;
            color: #4CAF50;
        }
        
        .status p {
            opacity: 0.9;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            opacity: 0.8;
        }
        
        .tech-stack {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .tech-badge {
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .tabs-nav {
                flex-direction: column;
                gap: 5px;
            }
            
            .tab-button {
                flex: none;
            }
            
            .projects {
                grid-template-columns: 1fr;
            }
            
            .project-links {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
<?php
    // Load sites data from fe_lamp_site.json and group by project type
    $sitesFile = '/opt/fe_lamp/fe_lamp_site.json';
    $sitesData = [ 'sites' => [] ];
    if (file_exists($sitesFile)) {
        $json = file_get_contents($sitesFile);
        $decoded = json_decode($json, true);
        if (is_array($decoded) && isset($decoded['sites']) && is_array($decoded['sites'])) {
            $sitesData = $decoded;
        }
    }
    // Load FE LAMP server info
    $feLampFile = '/opt/fe_lamp/fe_lamp.json';
    $feLamp = [];
    if (file_exists($feLampFile)) {
        $j2 = file_get_contents($feLampFile);
        $d2 = json_decode($j2, true);
        if (is_array($d2)) { $feLamp = $d2; }
    }

    function h($str) {
        return htmlspecialchars((string)$str, ENT_QUOTES, 'UTF-8');
    }

    // Group sites by type (JavaScript, WordPress, Laravel)
    $grouped = [
        'JavaScript' => [],
        'WordPress' => [],
        'Laravel' => [],
    ];

    foreach ($sitesData['sites'] as $domain => $info) {
        $type = isset($info['project_type']) ? $info['project_type'] : 'Unknown';
        $port = isset($info['port']) ? $info['port'] : 8080;
        $name = isset($info['name']) ? $info['name'] : (explode('.', $domain)[0] ?? $domain);
        $desc = isset($info['description']) ? $info['description'] : '';
        $url  = 'http://' . $domain . ':' . $port;

        if (isset($grouped[$type])) {
            $grouped[$type][] = [
                'name' => $name,
                'domain' => $domain,
                'url' => $url,
                'desc' => $desc,
                'port' => $port,
            ];
        }
    }
?>
    <div class="container">
        <div class="header">
            <h1>🚀 Four Elements Web Server</h1>
            <p>Test Server for all projects on your local machine. This is LAMP stack server.</p>
        </div>
        
        <div class="status">
            <h2>✅ Server Control</h2>
            <p id="serverStatus">Welcome to Four Elements Web Server! Use the controls below.</p>
            <div style="margin-top:12px; display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
                <button id="btnStart" style="padding:8px 14px;border:none;border-radius:8px;cursor:pointer;background:#4CAF50;color:#fff;">Start</button>
                <button id="btnStop" style="padding:8px 14px;border:none;border-radius:8px;cursor:pointer;background:#E53935;color:#fff;">Stop</button>
                <button id="btnRestart" style="padding:8px 14px;border:none;border-radius:8px;cursor:pointer;background:#FB8C00;color:#fff;">Restart</button>
                <button id="btnStatus" style="padding:8px 14px;border:none;border-radius:8px;cursor:pointer;background:#2196F3;color:#fff;">Status</button>
            </div>
        </div>
        
        <div class="top-nav" style="display:flex;gap:10px;justify-content:center;margin:10px 0 20px 0;">
            <button class="nav-button" data-nav="home" style="padding:10px 16px;border-radius:8px;border:none;cursor:pointer;">🏠 Home</button>
            <button class="nav-button" data-nav="information" style="padding:10px 16px;border-radius:8px;border:none;cursor:pointer;">ℹ️ Information</button>
            <button class="nav-button" data-nav="help" style="padding:10px 16px;border-radius:8px;border:none;cursor:pointer;">❓ Help</button>
        </div>

        <div class="nav-content" id="home">
        <div class="tabs-container">
            <!-- Tab Navigation -->
            <div class="tabs-nav">
                <button class="tab-button active" data-tab="javascript">🚀 JavaScript Projects</button>
                <button class="tab-button" data-tab="wordpress">🌐 WordPress Projects</button>
                <button class="tab-button" data-tab="laravel">⚡ Laravel Projects</button>
            </div>
            
            <!-- JavaScript Projects Tab -->
            <div id="javascript" class="tab-content active">
                <div class="projects">
                    <?php if (!empty($grouped['JavaScript'])): ?>
                        <?php foreach ($grouped['JavaScript'] as $site): ?>
                            <div class="project-card">
                                <h3>🎯 <?php echo h($site['name']); ?></h3>
                                <p><?php echo h($site['desc'] ?: 'JavaScript project'); ?></p>
                                <div class="project-links">
                                    <a href="<?php echo h($site['url']); ?>" class="project-link primary" target="_blank">🚀 Open</a>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div class="project-card"><p>No JavaScript projects found.</p></div>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- WordPress Projects Tab -->
            <div id="wordpress" class="tab-content">
                <div class="projects">
                    <?php if (!empty($grouped['WordPress'])): ?>
                        <?php foreach ($grouped['WordPress'] as $site): ?>
                            <div class="project-card">
                                <h3>🏷️ <?php echo h($site['name']); ?></h3>
                                <p><?php echo h($site['desc'] ?: 'WordPress project'); ?></p>
                                <div class="project-links">
                                    <a href="<?php echo h($site['url']); ?>" class="project-link primary" target="_blank">🌐 Development Site</a>
                                    <a href="<?php echo h($site['url']); ?>/wp-admin" class="project-link secondary" target="_blank">📱 Admin Panel</a>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div class="project-card"><p>No WordPress projects found.</p></div>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- Laravel Projects Tab -->
            <div id="laravel" class="tab-content">
                <div class="projects">
                    <?php if (!empty($grouped['Laravel'])): ?>
                        <?php foreach ($grouped['Laravel'] as $site): ?>
                            <div class="project-card">
                                <h3>⚡ <?php echo h($site['name']); ?></h3>
                                <p><?php echo h($site['desc'] ?: 'Laravel project'); ?></p>
                                <div class="project-links">
                                    <a href="<?php echo h($site['url']); ?>" class="project-link primary" target="_blank">🌐 Development Site</a>
                                    <a href="<?php echo h($site['url']); ?>/admin" class="project-link secondary" target="_blank">📱 Admin Panel</a>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div class="project-card"><p>No Laravel projects found.</p></div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
        </div>

        <div class="nav-content" id="information" style="display:none;">
            <div class="status">
                <h2>ℹ️ Server Information</h2>
                <p>Configuration loaded from /opt/fe_lamp/fe_lamp.json</p>
            </div>
            <div class="projects">
                <div class="project-card">
                    <h3>System</h3>
                    <p>
                        <?php
                        $sys = isset($feLamp['system']) && is_array($feLamp['system']) ? $feLamp['system'] : [];
                        function hv($arr, $k) { return htmlspecialchars(isset($arr[$k]) ? (string)$arr[$k] : '', ENT_QUOTES, 'UTF-8'); }
                        ?>
                        <strong>Apache Config:</strong> <?php echo hv($sys,'httpd_conf'); ?><br>
                        <strong>Document Root:</strong> <?php echo hv($sys,'doc_root'); ?><br>
                        <strong>Apache Port:</strong> <?php echo hv($sys,'apache_port'); ?><br>
                        <strong>PHP Version:</strong> <?php echo hv($sys,'php_version'); ?><br>
                        <strong>PHP ini:</strong> <?php echo hv($sys,'php_ini'); ?><br>
                        <strong>phpMyAdmin Path:</strong> <?php echo hv($sys,'pma_path'); ?><br>
                        <strong>phpMyAdmin Config:</strong> <?php echo hv($sys,'pma_config'); ?><br>
                        <strong>MySQL User:</strong> <?php echo hv($sys,'mysql_username'); ?><br>
                        <strong>MySQL Password:</strong> <?php echo hv($sys,'mysql_password'); ?><br>
                        <strong>Updated At:</strong> <?php echo hv($sys,'update_date'); ?><br>
                    </p>
                </div>
                <div class="project-card">
                    <h3>Components</h3>
                    <p>Installed components detected by FE LAMP:</p>
                    <ul>
                        <?php if (isset($feLamp['components']) && is_array($feLamp['components'])): ?>
                            <?php foreach ($feLamp['components'] as $c): ?>
                                <li>
                                    <?php echo htmlspecialchars(($c['name'] ?? 'component').' '.($c['version'] ?? ''), ENT_QUOTES, 'UTF-8'); ?>
                                    — bin: <?php echo htmlspecialchars($c['bin'] ?? '', ENT_QUOTES, 'UTF-8'); ?>
                                </li>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <li>No component information.</li>
                        <?php endif; ?>
                    </ul>
                </div>
            </div>
        </div>

        <div class="nav-content" id="help" style="display:none;">
            <div class="status">
                <h2>❓ Help</h2>
                <p>Common commands for FE LAMP CLI.</p>
            </div>
            <div class="projects">
                <div class="project-card">
                    <h3>Core</h3>
                    <div class="project-links" style="gap:6px;">
                        <code>fe_lamp status</code>
                        <code>fe_lamp install --db mysql</code>
                        <code>fe_lamp start | stop | restart</code>
                        <code>fe_lamp configure-apache --port 8080 --doc-root /opt/homebrew/var/www</code>
                        <code>fe_lamp show-apache-config</code>
                    </div>
                </div>
                <div class="project-card">
                    <h3>Sites</h3>
                    <div class="project-links" style="gap:6px;">
                        <code>fe_lamp_site</code>
                        <code>fe_lamp_site --help</code>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Four Elements Web Server - LAMP stack server</p>
            <div class="tech-stack">
                <span class="tech-badge">HTML5</span>
                <span class="tech-badge">CSS3</span>
                <span class="tech-badge">JavaScript</span>
                <span class="tech-badge">PHP</span>
                <span class="tech-badge">MySQL</span>
                <span class="tech-badge">LAMP</span>
            </div>
        </div>
    </div>
    
    <script>
        // Add some interactivity
        document.addEventListener('DOMContentLoaded', function() {
            // Inner tabs functionality
            const tabButtons = document.querySelectorAll('.tab-button');
            const tabContents = document.querySelectorAll('.tab-content');
            
            tabButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const targetTab = this.getAttribute('data-tab');
                    
                    // Remove active class from all buttons and contents
                    tabButtons.forEach(btn => btn.classList.remove('active'));
                    tabContents.forEach(content => content.classList.remove('active'));
                    
                    // Add active class to clicked button and corresponding content
                    this.classList.add('active');
                    document.getElementById(targetTab).classList.add('active');
                });
            });
            
            // Add click tracking
            const links = document.querySelectorAll('.project-link');
            links.forEach(link => {
                link.addEventListener('click', function(e) {
                    console.log('Navigating to:', this.href);
                });
            });
            
            // Add keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && e.target.classList.contains('project-link')) {
                    e.target.click();
                }
            });

            // Top navigation functionality
            const navButtons = document.querySelectorAll('.nav-button');
            const navContents = document.querySelectorAll('.nav-content');
            function setNav(target) {
                navButtons.forEach(btn => btn.classList.remove('active'));
                navContents.forEach(c => c.style.display = 'none');
                const btn = document.querySelector(`.nav-button[data-nav="${target}"]`);
                const content = document.getElementById(target);
                if (btn) btn.classList.add('active');
                if (content) content.style.display = 'block';
            }
            navButtons.forEach(btn => {
                btn.addEventListener('click', function() {
                    setNav(this.getAttribute('data-nav'));
                });
            });
            // default
            setNav('home');

            // Server control actions
            async function callApi(action) {
                const el = document.getElementById('serverStatus');
                try {
                    el.textContent = 'Processing ' + action + ' ...';
                    const res = await fetch('api.php?action=' + encodeURIComponent(action));
                    const data = await res.json();
                    if (data && data.ok) {
                        el.textContent = action + ' ok';
                    } else {
                        el.textContent = action + ' failed';
                    }
                } catch (e) {
                    el.textContent = action + ' error';
                }
            }
            const btnStart = document.getElementById('btnStart');
            const btnStop = document.getElementById('btnStop');
            const btnRestart = document.getElementById('btnRestart');
            const btnStatus = document.getElementById('btnStatus');
            if (btnStart) btnStart.addEventListener('click', () => callApi('lamp_start'));
            if (btnStop) btnStop.addEventListener('click', () => callApi('lamp_stop'));
            if (btnRestart) btnRestart.addEventListener('click', () => callApi('lamp_restart'));
            if (btnStatus) btnStatus.addEventListener('click', () => callApi('lamp_status'));
        });
    </script>
</body>
</html>
