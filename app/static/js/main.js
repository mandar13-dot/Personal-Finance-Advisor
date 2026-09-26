document.addEventListener("DOMContentLoaded", function () {
    const actionButtons = document.querySelectorAll("button.action-btn");
    const modal = document.getElementById("actionModal");
    const modalTitle = document.getElementById("modalTitle");
    const modalMessage = document.getElementById("modalMessage");
    const modalCloseBtn = document.getElementById("modalCloseBtn");
    const modalConfirmBtn = document.getElementById("modalConfirmBtn");

    if (actionButtons.length && modal) {
        actionButtons.forEach(function (btn) {
            btn.addEventListener("click", function () {
                const actionName = this.getAttribute("data-action") || "Feature";
                if (modalTitle) {
                    modalTitle.textContent = actionName;
                }
                if (modalMessage) {
                    modalMessage.textContent = `The "${actionName}" action placeholder is ready. It will be wired to the financial database logic in the upcoming step.`;
                }
                modal.style.display = "flex";
            });
        });

        function closeModal() {
            modal.style.display = "none";
        }

        if (modalCloseBtn) {
            modalCloseBtn.addEventListener("click", closeModal);
        }
        if (modalConfirmBtn) {
            modalConfirmBtn.addEventListener("click", closeModal);
        }

        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                closeModal();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && modal.style.display === "flex") {
                closeModal();
            }
        });
    }
});
