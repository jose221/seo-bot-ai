const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const express = require('express');
const { app, BrowserWindow, Notification, dialog, ipcMain } = require('electron');

const FRONTEND_PORT = 4001;
const API_PORT = 8010;
const API_OUTPUT_LIMIT = 40;
const AUTH_DEBUG_ENABLED = process.argv.includes('--auth-debug');

let frontendServer = null;
let apiProcess = null;
let apiOutputBuffer = [];
let authDebugLogPath = null;

function getApiRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'api');
  }
  return path.join(app.getAppPath(), 'api');
}

function getFrontendDistRoot() {
  return path.join(app.getAppPath(), 'dist', 'seo-bot-ai', 'browser');
}

function getIconPath() {
  return path.join(app.getAppPath(), 'desktop', 'resources', 'icon.png');
}

function getPreloadPath() {
  return path.join(app.getAppPath(), 'desktop', 'preload.cjs');
}

function getApiPidFilePath() {
  return path.join(app.getPath('userData'), 'fastapi.pid');
}

function getAuthDebugLogPath() {
  return path.join(app.getPath('desktop'), 'seo-bot-ai-auth-debug.log');
}

function appendAuthDebug(message, details) {
  if (!AUTH_DEBUG_ENABLED) {
    return;
  }

  const timestamp = new Date().toISOString();
  const serializedDetails = details === undefined ? '' : ` ${JSON.stringify(details)}`;
  const line = `[auth-debug] ${timestamp} ${message}${serializedDetails}`;

  console.log(line);

  if (!authDebugLogPath) {
    authDebugLogPath = getAuthDebugLogPath();
  }

  fs.appendFileSync(authDebugLogPath, `${line}\n`, 'utf8');
}

function appendApiOutput(prefix, chunk) {
  const text = chunk.toString();
  process[prefix === 'stderr' ? 'stderr' : 'stdout'].write(`[api] ${text}`);

  apiOutputBuffer.push(
    ...text
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean),
  );

  if (apiOutputBuffer.length > API_OUTPUT_LIMIT) {
    apiOutputBuffer = apiOutputBuffer.slice(-API_OUTPUT_LIMIT);
  }
}

function clearApiPidFile() {
  try {
    fs.unlinkSync(getApiPidFilePath());
  } catch (error) {
    if (error && error.code !== 'ENOENT') {
      throw error;
    }
  }
}

function persistApiPid(pid) {
  fs.writeFileSync(getApiPidFilePath(), String(pid), 'utf8');
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function cleanupPreviousApiProcess() {
  const pidFilePath = getApiPidFilePath();

  if (!fs.existsSync(pidFilePath)) {
    return;
  }

  const previousPid = Number.parseInt(fs.readFileSync(pidFilePath, 'utf8').trim(), 10);
  clearApiPidFile();

  if (!Number.isInteger(previousPid) || previousPid <= 0) {
    return;
  }

  try {
    process.kill(previousPid, 'SIGTERM');
    await sleep(1200);
  } catch (error) {
    if (!error || error.code !== 'ESRCH') {
      throw error;
    }
  }
}

async function hasReusableApiServer() {
  try {
    const response = await fetch(`http://127.0.0.1:${API_PORT}/health`);
    if (!response.ok) {
      return false;
    }

    const payload = await response.json();
    return payload?.service === 'SEO Bot AI' && payload?.status === 'healthy';
  } catch (error) {
    return false;
  }
}

function findPythonBinary(apiRoot) {
  const candidates = [
    process.env.SEO_BOT_PYTHON,
    path.join(apiRoot, '.desktop-python', 'bin', 'python3'),
    path.join(apiRoot, '.venv', 'bin', 'python3'),
    path.join(apiRoot, 'myenv', 'bin', 'python3'),
    'python3',
  ].filter(Boolean);

  const existing = candidates.find((candidate) => {
    if (candidate === 'python3') return true;
    return fs.existsSync(candidate);
  });

  return existing || 'python3';
}

function waitForHttp(url, timeoutMs = 60000, intervalMs = 500) {
  const startedAt = Date.now();

  return new Promise((resolve, reject) => {
    const check = async () => {
      try {
        const response = await fetch(url);
        if (response.ok) {
          resolve();
          return;
        }
      } catch (error) {
        // Keep retrying until timeout.
      }

      if (Date.now() - startedAt >= timeoutMs) {
        reject(new Error(`Timeout waiting for ${url}`));
        return;
      }

      setTimeout(check, intervalMs);
    };

    check();
  });
}

function startFrontendServer() {
  const distRoot = getFrontendDistRoot();
  const indexPath = path.join(distRoot, 'index.html');

  if (!fs.existsSync(indexPath)) {
    throw new Error(
      `No se encontró ${indexPath}. Ejecuta "npm run build:desktop:web" antes de abrir la app.`,
    );
  }

  const frontendApp = express();
  frontendApp.use(express.static(distRoot));
  frontendApp.use((_request, response) => {
    response.sendFile(indexPath);
  });

  return new Promise((resolve, reject) => {
    const server = frontendApp
      .listen(FRONTEND_PORT, '127.0.0.1', () => resolve(server))
      .on('error', reject);
  });
}

async function startApiServer() {
  const apiRoot = getApiRoot();
  if (!fs.existsSync(path.join(apiRoot, 'app', 'main.py'))) {
    throw new Error(`No se encontró la API en ${apiRoot}.`);
  }

  await cleanupPreviousApiProcess();

  if (await hasReusableApiServer()) {
    console.log(`[api] Reutilizando API existente en http://127.0.0.1:${API_PORT}`);
    return;
  }

  const pythonBin = findPythonBinary(apiRoot);
  const args = ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(API_PORT)];
  apiOutputBuffer = [];

  apiProcess = spawn(pythonBin, args, {
    cwd: apiRoot,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (apiProcess.pid) {
    persistApiPid(apiProcess.pid);
  }

  apiProcess.stdout.on('data', (chunk) => {
    appendApiOutput('stdout', chunk);
  });

  apiProcess.stderr.on('data', (chunk) => {
    appendApiOutput('stderr', chunk);
  });

  apiProcess.on('error', (error) => {
    clearApiPidFile();
    dialog.showErrorBox(
      'No se pudo iniciar FastAPI',
      `Error al ejecutar Python (${pythonBin}): ${error.message}`,
    );
    app.quit();
  });

  apiProcess.on('exit', (code) => {
    clearApiPidFile();
    if (!app.isQuiting) {
      const details = apiOutputBuffer.length
        ? `\n\nUltimas lineas:\n${apiOutputBuffer.join('\n')}`
        : '';
      dialog.showErrorBox(
        'API local detenida',
        `La API de FastAPI se cerró inesperadamente (exit code: ${code ?? 'desconocido'}).${details}`,
      );
      app.quit();
    }
  });
}

async function createWindow() {
  const iconPath = getIconPath();
  const preloadPath = getPreloadPath();

  if (process.platform === 'darwin' && fs.existsSync(iconPath) && app.dock) {
    app.dock.setIcon(iconPath);
  }

  const mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1200,
    minHeight: 760,
    title: 'SEO Bot AI',
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: fs.existsSync(preloadPath) ? preloadPath : undefined,
    },
  });

  const session = mainWindow.webContents.session;
  const authDebugUrls = [
    'http://127.0.0.1:4001/*',
    'http://localhost:4001/*',
    'http://127.0.0.1:8010/*',
    'http://localhost:8010/*',
    'https://auth-keycloak.herandro.com.mx/*',
  ];

  if (AUTH_DEBUG_ENABLED) {
    appendAuthDebug('Auth debug enabled', { logPath: getAuthDebugLogPath() });

    session.webRequest.onBeforeRequest({ urls: authDebugUrls }, (details, callback) => {
      appendAuthDebug('onBeforeRequest', {
        method: details.method,
        url: details.url,
        resourceType: details.resourceType,
      });
      callback({});
    });

    session.webRequest.onBeforeSendHeaders({ urls: authDebugUrls }, (details, callback) => {
      appendAuthDebug('onBeforeSendHeaders', {
        method: details.method,
        url: details.url,
        requestHeaders: details.requestHeaders,
      });
      callback({ requestHeaders: details.requestHeaders });
    });

    session.webRequest.onHeadersReceived({ urls: authDebugUrls }, (details, callback) => {
      appendAuthDebug('onHeadersReceived', {
        statusCode: details.statusCode,
        url: details.url,
        responseHeaders: details.responseHeaders,
      });
      callback({ responseHeaders: details.responseHeaders });
    });

    session.webRequest.onCompleted({ urls: authDebugUrls }, (details) => {
      appendAuthDebug('onCompleted', {
        method: details.method,
        statusCode: details.statusCode,
        url: details.url,
        fromCache: details.fromCache,
      });
    });

    session.webRequest.onErrorOccurred({ urls: authDebugUrls }, (details) => {
      appendAuthDebug('onErrorOccurred', {
        method: details.method,
        error: details.error,
        url: details.url,
      });
    });

    mainWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
      appendAuthDebug('console-message', { level, message, line, sourceId });
    });

    mainWindow.webContents.on('did-start-navigation', (_event, url, isInPlace, isMainFrame) => {
      appendAuthDebug('did-start-navigation', { url, isInPlace, isMainFrame });
    });

    mainWindow.webContents.on('did-redirect-navigation', (_event, url, isInPlace, isMainFrame) => {
      appendAuthDebug('did-redirect-navigation', { url, isInPlace, isMainFrame });
    });

    mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
      appendAuthDebug('did-fail-load', { errorCode, errorDescription, validatedURL });
    });

    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  await mainWindow.loadURL(`http://127.0.0.1:${FRONTEND_PORT}`);
}

ipcMain.on('desktop-notifications:show', (event, payload) => {
  if (!payload?.title || !Notification.isSupported()) {
    return;
  }

  const notification = new Notification({
    title: payload.title,
    body: payload.body || '',
    icon: fs.existsSync(getIconPath()) ? getIconPath() : undefined,
    silent: false,
  });

  notification.on('click', () => {
    const targetWindow = BrowserWindow.fromWebContents(event.sender);
    if (!targetWindow) {
      return;
    }

    if (targetWindow.isMinimized()) {
      targetWindow.restore();
    }

    targetWindow.show();
    targetWindow.focus();
    targetWindow.webContents.send('desktop-notifications:click', {
      route: payload.route,
    });
  });

  notification.show();
});

function stopServices() {
  if (frontendServer) {
    frontendServer.close();
    frontendServer = null;
  }

  if (apiProcess && apiProcess.pid) {
    try {
      if (apiProcess.exitCode === null && apiProcess.signalCode === null && !apiProcess.killed) {
        process.kill(apiProcess.pid, 'SIGTERM');
      }
    } catch (error) {
      if (!error || error.code !== 'ESRCH') {
        throw error;
      }
    }
    apiProcess = null;
  }

  clearApiPidFile();
}

app.on('before-quit', () => {
  app.isQuiting = true;
  stopServices();
});

app.whenReady().then(async () => {
  try {
    frontendServer = await startFrontendServer();
    await startApiServer();

    await waitForHttp(`http://127.0.0.1:${API_PORT}/health`);
    await createWindow();

    app.on('activate', async () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        await createWindow();
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dialog.showErrorBox('No se pudo iniciar SEO Bot AI', message);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
