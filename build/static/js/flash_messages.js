document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll(".flash-message");
    
    flashMessages.forEach((message, index) => {
        message.style.animationDelay = `${index * 0.1}s`;
        
        setTimeout(() => {
            message.style.animation = "slideOut 0.3s ease forwards";
            setTimeout(() => {
                message.remove();
                const container = document.querySelector(".flash-messages");
                if (container && container.children.length === 0) {
                    container.remove();
                }
            }, 300);
        }, 5000);
        
        message.addEventListener("click", () => {
            message.style.animation = "slideOut 0.3s ease forwards";
            setTimeout(() => message.remove(), 300);
        });
    });
});