
const API_BASE_URL = "";

// Chart instances
let transactionChart = null;
let distributionChart = null;

// Store available wallets
let wallets = [];
let currentTransactions = [];

// DOM helper
function getElement(id) {
    return document.getElementById(id);
}


// 1. NAVIGATION
document.querySelectorAll("[data-section]").forEach(button => {

    button.addEventListener("click", function (event) {
        event.preventDefault();

        const section = this.dataset.section;

        document.querySelectorAll(".page-section").forEach(page => {
            page.classList.add("hidden");
        });

        getElement(`${section}-section`).classList.remove("hidden");

        document.querySelectorAll(".nav-link").forEach(link => {
            link.classList.remove("active");
        });

        document.querySelectorAll(".nav-link").forEach(link => {
            if (link.dataset.section === section) {
                link.classList.add("active");
            }
        });
    });

});


// 2. FETCH ALL WALLETS
async function loadWallets() {

    try {
        const response = await fetch(`${API_BASE_URL}/wallets`);

        if (!response.ok) {
            throw new Error("Unable to load wallets");
        }

        wallets = await response.json();

        const selector = getElement("wallet-selector");

        selector.innerHTML = "";

        wallets.forEach(wallet => {

            const option = document.createElement("option");

            option.value = wallet.wallet_id;

            option.textContent =
                `Wallet ${wallet.wallet_id} - ${wallet.currency}`;

            selector.appendChild(option);

        });

        if (wallets.length > 0) {
            await loadDashboard(wallets[0].wallet_id);
        } else {
            selector.innerHTML = '<option value="">No wallets found</option>';
        }

    } catch (error) {
        console.error(error);
        alert("Could not connect to LedgerX backend.");
    }
}


// 3. LOAD SELECTED WALLET DASHBOARD
async function loadDashboard(walletId) {

    if (!walletId) return;

    try {

        const [walletResponse, transactionResponse] =
            await Promise.all([

                fetch(`${API_BASE_URL}/wallets/${walletId}`),

                fetch(`${API_BASE_URL}/wallets/${walletId}/transactions`)

            ]);

        if (!walletResponse.ok || !transactionResponse.ok) {
            throw new Error("Unable to load wallet information");
        }

        const wallet = await walletResponse.json();

        const transactions = await transactionResponse.json();

        currentTransactions = transactions;

        // Update balance
        getElement("wallet-balance").textContent =
            formatMoney(wallet.balance, wallet.currency);

        getElement("wallet-currency").textContent =
            `${wallet.currency} Wallet`;

        // Update form defaults
        getElement("sender-wallet").value = walletId;
        getElement("deposit-wallet").value = walletId;

        // Update statistics
        updateStatistics(walletId, transactions);

        // Update tables
        renderRecentTransactions(walletId, transactions);
        renderAllTransactions(walletId, transactions);

        // Update charts
        updateCharts(walletId, transactions);

    } catch (error) {
        console.error(error);
        alert("Could not load wallet dashboard.");
    }
}


// 4. FORMAT MONEY
function formatMoney(amount, currency = "INR") {

    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: currency,
        minimumFractionDigits: 2
    }).format(Number(amount));

}


// 5. CALCULATE DASHBOARD STATISTICS
function updateStatistics(walletId, transactions) {

    let totalSent = 0;
    let totalReceived = 0;

    transactions.forEach(transaction => {

        if (transaction.sender_wallet_id === Number(walletId)) {
            totalSent += Number(transaction.amount);
        }

        if (transaction.receiver_wallet_id === Number(walletId)) {
            totalReceived += Number(transaction.amount);
        }

    });

    getElement("total-sent").textContent =
        formatMoney(totalSent);

    getElement("total-received").textContent =
        formatMoney(totalReceived);

    getElement("total-transactions").textContent =
        transactions.length;

}


// 6. DISPLAY RECENT TRANSACTIONS
function renderRecentTransactions(walletId, transactions) {

    const table = getElement("recent-transactions");

    table.innerHTML = "";

    const recent = transactions.slice(0, 6);

    if (recent.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="5">No transactions found.</td>
            </tr>
        `;
        return;
    }

    recent.forEach(transaction => {

        const isSent =
            transaction.sender_wallet_id === Number(walletId);

        const type = isSent ? "Sent" : "Received";

        const amountClass = isSent
            ? "transaction-debit"
            : "transaction-credit";

        const sign = isSent ? "−" : "+";

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>#${transaction.id}</td>
            <td>${type}</td>
            <td class="${amountClass}">
                ${sign} ${formatMoney(transaction.amount)}
            </td>
            <td>
                <span class="status-badge">
                    ${transaction.status}
                </span>
            </td>
            <td>Wallet ${isSent
                ? transaction.receiver_wallet_id
                : transaction.sender_wallet_id}
            </td>
        `;

        table.appendChild(row);

    });

}


// 7. DISPLAY ALL TRANSACTIONS
function renderAllTransactions(walletId, transactions) {

    const table = getElement("all-transactions");

    table.innerHTML = "";

    if (transactions.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="4">No transactions found.</td>
            </tr>
        `;
        return;
    }

    transactions.forEach(transaction => {

        const isSent =
            transaction.sender_wallet_id === Number(walletId);

        const type = isSent ? "Sent" : "Received";

        const amountClass = isSent
            ? "transaction-debit"
            : "transaction-credit";

        const sign = isSent ? "−" : "+";

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>#${transaction.id}</td>
            <td>${type}</td>
            <td class="${amountClass}">
                ${sign} ${formatMoney(transaction.amount)}
            </td>
            <td>
                <span class="status-badge">
                    ${transaction.status}
                </span>
            </td>
        `;

        table.appendChild(row);

    });

}


// 8. UPDATE CHARTS
function updateCharts(walletId, transactions) {

    let totalSent = 0;
    let totalReceived = 0;

    transactions.forEach(transaction => {

        if (transaction.sender_wallet_id === Number(walletId)) {
            totalSent += Number(transaction.amount);
        }

        if (transaction.receiver_wallet_id === Number(walletId)) {
            totalReceived += Number(transaction.amount);
        }

    });

    // Destroy old charts before creating new ones
    if (transactionChart) {
        transactionChart.destroy();
    }

    if (distributionChart) {
        distributionChart.destroy();
    }

    // Bar chart
    const recent = transactions.slice(0, 6).reverse();

    transactionChart = new Chart(
        getElement("transaction-chart"),
        {
            type: "bar",

            data: {
                labels: recent.map(t => `#${t.id}`),

                datasets: [
                    {
                        label: "Transaction Amount (INR)",

                        data: recent.map(t => Number(t.amount)),

                        backgroundColor: "#a3c625",

                        borderRadius: 6
                    }
                ]
            },

            options: {
                responsive: true,

                plugins: {
                    legend: {
                        display: false
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        }
    );


    // Doughnut chart
    distributionChart = new Chart(
        getElement("distribution-chart"),
        {
            type: "doughnut",

            data: {
                labels: ["Sent", "Received"],

                datasets: [
                    {
                        data: [totalSent, totalReceived],

                        backgroundColor: [
                            "#e45b68",
                            "#a3c625"
                        ],

                        borderWidth: 0
                    }
                ]
            },

            options: {
                responsive: true,

                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        }
    );

}


// 9. WALLET SELECTION
getElement("wallet-selector").addEventListener(
    "change",
    async function () {

        await loadDashboard(Number(this.value));

    }
);


// 10. SEND MONEY
getElement("transfer-form").addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        const senderId = Number(
            getElement("sender-wallet").value
        );

        const receiverId = Number(
            getElement("receiver-wallet").value
        );

        const amount = Number(
            getElement("transfer-amount").value
        );

        const message = getElement("transfer-message");

        try {

            const response = await fetch(
                `${API_BASE_URL}/transfers`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "Idempotency-Key": crypto.randomUUID()
                    },

                    body: JSON.stringify({
                        sender_wallet_id: senderId,
                        receiver_wallet_id: receiverId,
                        amount: amount
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Transfer failed");
            }

            message.style.color = "#16a36a";

            message.textContent =
                `Transfer successful! Transaction ID: ${result.id}`;

            this.reset();

            await loadWallets();

            getElement("wallet-selector").value = senderId;

            await loadDashboard(senderId);

        } catch (error) {

            message.style.color = "#e45b68";

            message.textContent = error.message;

        }

    }
);


// 11. DEPOSIT MONEY
getElement("deposit-form").addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        const walletId = Number(
            getElement("deposit-wallet").value
        );

        const amount = Number(
            getElement("deposit-amount").value
        );

        const message = getElement("deposit-message");

        try {

            const response = await fetch(
                `${API_BASE_URL}/wallets/fund`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        wallet_id: walletId,
                        amount: amount
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Deposit failed");
            }

            message.style.color = "#16a36a";

            message.textContent =
                `Deposit successful! Transaction ID: ${result.id}`;

            this.reset();

            await loadWallets();

            getElement("wallet-selector").value = walletId;

            await loadDashboard(walletId);

        } catch (error) {

            message.style.color = "#e45b68";

            message.textContent = error.message;

        }

    }
);


// 12. START APPLICATION
loadWallets();
