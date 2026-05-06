const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desktopNotifications', {
  notify(payload) {
    ipcRenderer.send('desktop-notifications:show', payload);
  },
  onClick(callback) {
    const handler = (_event, payload) => callback(payload);
    ipcRenderer.on('desktop-notifications:click', handler);
    return () => {
      ipcRenderer.removeListener('desktop-notifications:click', handler);
    };
  },
});
