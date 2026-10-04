const API_BASE_URL = "https://roundtable-ai-yhf2.onrender.com";
const ROOM_ID = "room102";

document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // ELEMENTS
    // =====================================================

    const openBtn = document.getElementById("askMeetingBtn");

    const chatbot = document.getElementById("chatbot");

    const closeBtn = document.getElementById("closeBtn");

    const minimizeBtn =
        document.getElementById("minimizeBtn");

    const chatMessages =
        document.getElementById("chatMessages");

    const chatInput =
        document.getElementById("chatInput");

    const sendBtn =
        document.getElementById("sendBtn");

    const typing =
        document.getElementById("typing");

    const welcomeSection =
        document.getElementById("welcomeSection");


    // =====================================================
    // OPEN CHAT
    // =====================================================

    openBtn.addEventListener("click", () => {

        chatbot.classList.add("open");

        openBtn.style.display = "none";

        if (chatInput) {
            setTimeout(() => {
                chatInput.focus();
            }, 200);
        }

    });


    // =====================================================
    // CLOSE CHAT
    // =====================================================

    closeBtn.addEventListener("click", () => {

        chatbot.classList.remove("open");

        openBtn.style.display = "flex";

    });


    // =====================================================
    // MINIMIZE
    // =====================================================

    minimizeBtn.addEventListener("click", () => {

        chatbot.classList.toggle("minimized");

    });


    // =====================================================
    // ESCAPE HTML
    // =====================================================

    function escapeHtml(text) {

        const div =
            document.createElement("div");

        div.textContent = text ?? "";

        return div.innerHTML;
    }


    // =====================================================
    // ADD MESSAGE
    // =====================================================

    function addMessage(text, type) {

        const message =
            document.createElement("div");

        message.className =
            `message ${type}`;

        message.innerHTML = `
            <div class="message-content">
                ${escapeHtml(text)}
            </div>
        `;

        chatMessages.appendChild(message);

        chatMessages.scrollTop =
            chatMessages.scrollHeight;
    }


    // =====================================================
    // SHOW TYPING
    // =====================================================

    function showTyping() {

        typing.style.display = "block";

        chatMessages.scrollTop =
            chatMessages.scrollHeight;
    }


    // =====================================================
    // HIDE TYPING
    // =====================================================

    function hideTyping() {

        typing.style.display = "none";
    }


    // =====================================================
    // EVIDENCE
    // =====================================================

    function showEvidence(evidence) {

        if (
            !Array.isArray(evidence) ||
            evidence.length === 0
        ) {
            return;
        }

        const evidenceBox =
            document.createElement("div");

        evidenceBox.className =
            "evidence-box";

        evidenceBox.innerHTML = `
            <strong>Meeting Evidence</strong>

            ${evidence.map(item => {

                return `
                    <div class="evidence-item">
                        <b>
                            ${escapeHtml(
                                item.speaker || ""
                            )}
                        </b>

                        <div>
                            ${escapeHtml(
                                item.text || ""
                            )}
                        </div>
                    </div>
                `;

            }).join("")}
        `;

        chatMessages.appendChild(evidenceBox);

        chatMessages.scrollTop =
            chatMessages.scrollHeight;
    }


    // =====================================================
    // SEND MESSAGE
    // =====================================================

    async function sendMessage(text) {

        const message =
            text.trim();

        if (!message) {
            return;
        }


        // Show chatbot if somehow closed

        if (!chatbot.classList.contains("open")) {

            chatbot.classList.add("open");

            openBtn.style.display = "none";
        }


        // Remove welcome screen after first question

        if (welcomeSection) {

            welcomeSection.style.display =
                "none";
        }


        // User message

        addMessage(
            message,
            "user"
        );


        // Clear input

        chatInput.value = "";

        sendBtn.disabled = true;

        showTyping();


        try {

            const response =
                await fetch(
                    `${API_BASE_URL}/chat`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            room_id:
                                ROOM_ID,

                            message:
                                message

                        })
                    }
                );


            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );
            }


            const data =
                await response.json();


            hideTyping();


            // Backend response

            const answer =
                data.answer ||
                data.response ||
                data.message ||
                "I couldn't generate a response.";


            addMessage(
                answer,
                "bot"
            );


            // Meeting evidence

            showEvidence(
                data.evidence
            );


        } catch (error) {

            console.error(
                "Chat API error:",
                error
            );

            hideTyping();

            addMessage(
                "I couldn't connect to the AI server. Please try again.",
                "bot"
            );

        } finally {

            sendBtn.disabled = false;

            chatInput.focus();

        }

    }


    // =====================================================
    // SEND BUTTON
    // =====================================================

    sendBtn.addEventListener(
        "click",
        () => {

            sendMessage(
                chatInput.value
            );

        }
    );


    // =====================================================
    // ENTER KEY
    // =====================================================

    chatInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage(
                    chatInput.value
                );

            }

        }
    );


    // =====================================================
    // QUICK ACTIONS
    // =====================================================

    document
        .querySelectorAll(".quick-action")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const question =
                        button.dataset.question;

                    sendMessage(
                        question
                    );

                }
            );

        });


    // =====================================================
    // DEBUG
    // =====================================================

    console.log(
        "Roundtable AI frontend loaded successfully."
    );

    console.log(
        "Backend:",
        API_BASE_URL
    );

});