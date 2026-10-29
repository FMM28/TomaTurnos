const socket = io({
    transports: ["websocket"],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

socket.on("cola_actualizada", () => {
    location.reload();
});

setInterval(() => {
    location.reload();
}, 30000);