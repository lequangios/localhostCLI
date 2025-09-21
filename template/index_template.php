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
            <h2>✅ Server is Running</h2>
            <p>Welcome to Four Elements Web Server! Choose a project to start testing.</p>
        </div>
        
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
            // Tab functionality
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
        });
    </script>
</body>
</html>
