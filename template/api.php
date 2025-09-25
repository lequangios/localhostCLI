<?php
// Simple local API gateway to FE LAMP CLIs (fe_lamp, fe_lamp_site)
// Note: Intended for local development. Do not expose publicly.

header('Content-Type: application/json; charset=utf-8');

// Ensure PATH has Homebrew bin for CLI binaries
$envPath = getenv('PATH');
$brewPaths = ['/opt/homebrew/bin', '/usr/local/bin'];
foreach ($brewPaths as $p) {
    if (strpos($envPath, $p) === false) {
        $envPath = $p . PATH_SEPARATOR . $envPath;
    }
}
putenv('PATH=' . $envPath);

// Helpers
function read_json_body(): array {
    $raw = file_get_contents('php://input');
    if (!$raw) return [];
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
}

function respond($data, int $code = 200): void {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function run_command(array $cmdParts, int $timeoutSeconds = 60): array {
    // Build safely escaped command
    $parts = [];
    foreach ($cmdParts as $i => $part) {
        if ($i === 0) {
            // Program name: basic sanitize
            $parts[] = escapeshellcmd($part);
        } else {
            $parts[] = escapeshellarg((string)$part);
        }
    }
    $cmd = implode(' ', $parts) . ' 2>&1';

    // Use proc_open to allow timeout
    $descriptors = [
        1 => ['pipe', 'w'],
        2 => ['pipe', 'w'],
    ];
    $proc = proc_open($cmd, $descriptors, $pipes);
    if (!is_resource($proc)) {
        return ['ok' => false, 'cmd' => $cmd, 'code' => -1, 'out' => '', 'err' => 'proc_open failed'];
    }

    $start = time();
    $output = '';
    stream_set_blocking($pipes[1], false);
    $status = proc_get_status($proc);
    while ($status['running']) {
        $chunk = stream_get_contents($pipes[1]);
        if ($chunk !== false && $chunk !== '') {
            $output .= $chunk;
        }
        if ((time() - $start) > $timeoutSeconds) {
            proc_terminate($proc);
            fclose($pipes[1]);
            if (isset($pipes[2])) @fclose($pipes[2]);
            return ['ok' => false, 'cmd' => $cmd, 'code' => 124, 'out' => $output, 'err' => 'timeout'];
        }
        usleep(100000);
        $status = proc_get_status($proc);
    }

    $exitCode = $status['exitcode'] ?? 0;
    $chunk = stream_get_contents($pipes[1]);
    if ($chunk !== false && $chunk !== '') $output .= $chunk;
    fclose($pipes[1]);
    if (isset($pipes[2])) @fclose($pipes[2]);
    proc_close($proc);

    return ['ok' => $exitCode === 0, 'cmd' => $cmd, 'code' => $exitCode, 'out' => $output, 'err' => ''];
}

// Routing
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$queryAction = isset($_GET['action']) ? (string)$_GET['action'] : null;
$body = ($method === 'POST') ? read_json_body() : [];
$action = $body['action'] ?? $queryAction ?? '';

// Whitelist basic actions
$whitelist = [
    'lamp_status' => ['fe_lamp', ['status']],
    'lamp_restart' => ['fe_lamp', ['restart']],
    'lamp_start' => ['fe_lamp', ['start']],
    'lamp_stop' => ['fe_lamp', ['stop']],
    'site_list' => ['fe_lamp_site', ['list']],
    'site_vhost_status' => ['fe_lamp_site', ['vhost-status']],
    'site_help' => ['fe_lamp_site', ['--help']],
];

// Generic run: { action: 'run', tool: 'fe_lamp'|'fe_lamp_site', args: [...] }
if ($action === 'run') {
    $tool = isset($body['tool']) ? (string)$body['tool'] : '';
    $args = isset($body['args']) && is_array($body['args']) ? $body['args'] : [];
    if (!in_array($tool, ['fe_lamp', 'fe_lamp_site'], true)) {
        respond(['ok' => false, 'error' => 'tool_not_allowed'], 400);
    }
    // Validate arguments are simple scalars
    $safeArgs = [];
    foreach ($args as $a) {
        if (is_scalar($a)) {
            $safeArgs[] = (string)$a;
        }
    }
    $res = run_command(array_merge([$tool], $safeArgs));
    respond([
        'ok' => $res['ok'],
        'action' => 'run',
        'tool' => $tool,
        'cmd' => $res['cmd'],
        'code' => $res['code'],
        'output' => $res['out'],
        'php' => PHP_VERSION,
        'path' => getenv('PATH'),
    ], $res['ok'] ? 200 : 500);
}

// Whitelisted actions
if (isset($whitelist[$action])) {
    [$tool, $fixedArgs] = $whitelist[$action];
    $res = run_command(array_merge([$tool], $fixedArgs));
    respond([
        'ok' => $res['ok'],
        'action' => $action,
        'cmd' => $res['cmd'],
        'code' => $res['code'],
        'output' => $res['out'],
        'php' => PHP_VERSION,
        'path' => getenv('PATH'),
    ], $res['ok'] ? 200 : 500);
}

// Dynamic site actions
if ($action === 'site_delete') {
    // Accept domain from GET or POST
    $domain = isset($body['domain']) ? (string)$body['domain'] : (isset($_GET['domain']) ? (string)$_GET['domain'] : '');
    if ($domain === '') {
        respond(['ok' => false, 'error' => 'missing_domain'], 400);
    }
    $args = ['delete', '--domain', $domain];
    $res = run_command(array_merge(['fe_lamp_site'], $args));
    respond([
        'ok' => $res['ok'],
        'action' => $action,
        'cmd' => $res['cmd'],
        'code' => $res['code'],
        'output' => $res['out'],
    ], $res['ok'] ? 200 : 500);
}

if ($action === 'site_create') {
    // Accept fields: name, path, description, type
    $name = isset($body['name']) ? (string)$body['name'] : (isset($_GET['name']) ? (string)$_GET['name'] : '');
    $path = isset($body['path']) ? (string)$body['path'] : (isset($_GET['path']) ? (string)$_GET['path'] : '');
    $description = isset($body['description']) ? (string)$body['description'] : (isset($_GET['description']) ? (string)$_GET['description'] : '');
    $type = isset($body['type']) ? (string)$body['type'] : (isset($_GET['type']) ? (string)$_GET['type'] : '');

    if ($name === '' || $path === '') {
        respond(['ok' => false, 'error' => 'missing_name_or_path'], 400);
    }
    $args = ['create'];
    // Only push flags if provided; flags depend on CLI implementation
    if ($name !== '') { $args[] = '--name'; $args[] = $name; }
    if ($path !== '') { $args[] = '--path'; $args[] = $path; }
    if ($description !== '') { $args[] = '--desc'; $args[] = $description; }
    if ($type !== '') { $args[] = '--type'; $args[] = $type; }

    $res = run_command(array_merge(['fe_lamp_site'], $args), 120);
    respond([
        'ok' => $res['ok'],
        'action' => $action,
        'cmd' => $res['cmd'],
        'code' => $res['code'],
        'output' => $res['out'],
    ], $res['ok'] ? 200 : 500);
}

// Help / default
respond([
    'ok' => true,
    'message' => 'FE LAMP API. Use POST {action:"run", tool:"fe_lamp|fe_lamp_site", args:[...] } or GET ?action=lamp_status|lamp_restart|lamp_start|lamp_stop|site_list|site_vhost_status|site_help|site_delete&domain=...|site_create&name=...&path=...&type=...&description=...',
    'php' => PHP_VERSION,
]);
?>

