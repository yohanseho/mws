// EVM Multi Pengirim JavaScript

class EVMMultiSender {
    constructor() {
        this.wallets = [];
        this.selectedNetwork = null;
        this.balances = [];
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Import private keys
        document.getElementById('importBtn').addEventListener('click', () => {
            this.importPrivateKeys();
        });

        // Network selection
        document.getElementById('networkSelect').addEventListener('change', (e) => {
            this.handleNetworkChange(e.target.value);
        });

        // Load balances
        document.getElementById('loadBalancesBtn').addEventListener('click', () => {
            this.loadBalances();
        });

        // Send transactions
        document.getElementById('sendTransactionsBtn').addEventListener('click', () => {
            this.sendTransactions();
        });

        // Clear session
        document.getElementById('clearSessionBtn').addEventListener('click', () => {
            this.clearSession();
        });
    }

    showLoading(text = 'Memproses...') {
        document.getElementById('loadingText').textContent = text;
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }

    hideLoading() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }

    showAlert(message, type = 'danger') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.container');
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    async importPrivateKeys() {
        const fileInput = document.getElementById('privateKeyFile');
        const file = fileInput.files[0];

        if (!file) {
            this.showAlert('Silakan pilih file terlebih dahulu.');
            return;
        }

        if (!file.name.endsWith('.txt')) {
            this.showAlert('Silakan pilih file .txt.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        this.showLoading('Mengimpor private key...');

        try {
            const response = await fetch('/import_keys', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.wallets = data.wallets;
                this.displayWallets();
                this.showAlert(`Berhasil mengimpor ${data.count} wallet!`, 'success');
                document.getElementById('networkSection').style.display = 'block';
            } else {
                this.showAlert(data.error || 'Gagal mengimpor private key.');
            }
        } catch (error) {
            console.error('Error importing keys:', error);
            this.showAlert('Terjadi kesalahan jaringan saat mengimpor key.');
        } finally {
            this.hideLoading();
        }
    }

    displayWallets() {
        const container = document.getElementById('walletsContainer');
        const walletsList = document.getElementById('walletsList');

        if (this.wallets.length === 0) {
            walletsList.style.display = 'none';
            return;
        }

        const walletsHtml = this.wallets.map((wallet, index) => `
            <div class="wallet-item">
                <small class="text-muted">#${index + 1}</small> ${wallet.address}
            </div>
        `).join('');

        container.innerHTML = walletsHtml;
        walletsList.style.display = 'block';
    }

    handleNetworkChange(networkValue) {
        const customFields = document.getElementById('customNetworkFields');
        
        if (networkValue === 'custom') {
            customFields.style.display = 'block';
        } else {
            customFields.style.display = 'none';
        }

        this.selectedNetwork = networkValue;
    }

    getNetworkConfig() {
        const networkSelect = document.getElementById('networkSelect');
        const selectedValue = networkSelect.value;

        if (!selectedValue) {
            throw new Error('Silakan pilih jaringan terlebih dahulu.');
        }

        const predefinedNetworks = {
            'ethereum': {
                name: 'Ethereum Mainnet',
                rpc_url: 'https://eth.llamarpc.com',
                chain_id: 1,
                symbol: 'ETH',
                explorer: 'https://etherscan.io'
            },
            'sepolia': {
                name: 'Sepolia Testnet',
                rpc_url: 'https://ethereum-sepolia-rpc.publicnode.com',
                chain_id: 11155111,
                symbol: 'ETH',
                explorer: 'https://sepolia.etherscan.io'
            },
            'holesky': {
                name: 'Holesky Testnet',
                rpc_url: 'https://ethereum-holesky.publicnode.com',
                chain_id: 17000,
                symbol: 'ETH',
                explorer: 'https://holesky.etherscan.io'
            },
            'monad': {
                name: 'Monad Testnet',
                rpc_url: 'https://testnet-rpc.monad.xyz',
                chain_id: 41454,
                symbol: 'MON',
                explorer: 'https://testnet-explorer.monad.xyz'
            }
        };

        if (selectedValue === 'custom') {
            const rpcUrl = document.getElementById('customRpc').value.trim();
            const chainId = parseInt(document.getElementById('customChainId').value);
            const symbol = document.getElementById('customSymbol').value.trim();
            const explorer = document.getElementById('customExplorer').value.trim();

            if (!rpcUrl || !chainId || !symbol) {
                throw new Error('Silakan isi semua field jaringan khusus yang diperlukan.');
            }

            return {
                name: 'Jaringan Khusus',
                rpc_url: rpcUrl,
                chain_id: chainId,
                symbol: symbol,
                explorer: explorer || ''
            };
        }

        return predefinedNetworks[selectedValue];
    }

    async loadBalances() {
        if (this.wallets.length === 0) {
            this.showAlert('Silakan impor wallet terlebih dahulu.');
            return;
        }

        try {
            const networkConfig = this.getNetworkConfig();
            this.showLoading('Memuat saldo wallet...');

            const response = await fetch('/get_balances', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    network: networkConfig
                })
            });

            const data = await response.json();

            if (data.success) {
                this.balances = data.balances;
                this.displayBalances(networkConfig.symbol);
                this.showAlert('Saldo berhasil dimuat!', 'success');
                document.getElementById('transferSection').style.display = 'block';
            } else {
                this.showAlert(data.error || 'Gagal memuat saldo.');
            }
        } catch (error) {
            console.error('Error loading balances:', error);
            this.showAlert(error.message || 'Error memuat saldo.');
        } finally {
            this.hideLoading();
        }
    }

    displayBalances(symbol) {
        const container = document.getElementById('balancesContainer');
        const balancesList = document.getElementById('balancesList');

        if (this.balances.length === 0) {
            balancesList.style.display = 'none';
            return;
        }

        const balancesHtml = this.balances.map((balance, index) => `
            <div class="balance-item ${balance.error ? 'text-danger' : ''}">
                <div class="balance-address">
                    <small class="text-muted">#${index + 1}</small><br>
                    ${balance.address}
                    ${balance.error ? `<div class="error-text">${balance.error}</div>` : ''}
                </div>
                <div class="balance-amount">
                    ${balance.balance_formatted} ${symbol}
                </div>
            </div>
        `).join('');

        container.innerHTML = balancesHtml;
        balancesList.style.display = 'block';
    }

    async sendTransactions() {
        if (this.wallets.length === 0) {
            this.showAlert('Silakan impor wallet terlebih dahulu.');
            return;
        }

        if (this.balances.length === 0) {
            this.showAlert('Silakan muat saldo terlebih dahulu.');
            return;
        }

        const recipientAddress = document.getElementById('recipientAddress').value.trim();
        if (!recipientAddress) {
            this.showAlert('Silakan masukkan alamat penerima.');
            return;
        }

        // Validate Ethereum address format
        if (!/^0x[a-fA-F0-9]{40}$/.test(recipientAddress)) {
            this.showAlert('Silakan masukkan alamat Ethereum yang valid.');
            return;
        }

        const selectedPercentage = document.querySelector('input[name="percentage"]:checked');
        if (!selectedPercentage) {
            this.showAlert('Silakan pilih persentase jumlah.');
            return;
        }

        const percentage = parseInt(selectedPercentage.value);

        try {
            const networkConfig = this.getNetworkConfig();
            
            const confirmed = confirm(
                `Apakah Anda yakin ingin mengirim ${percentage === 100 ? 'MAKSIMAL' : percentage + '%'} ` +
                `dari saldo setiap wallet ke ${recipientAddress}?\n\n` +
                `Ini akan mempengaruhi ${this.wallets.length} wallet di ${networkConfig.name}.`
            );

            if (!confirmed) {
                return;
            }

            this.showLoading('Mengirim transaksi... Ini mungkin memakan waktu.');

            const response = await fetch('/send_transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    network: networkConfig,
                    percentage: percentage,
                    recipient_address: recipientAddress
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data.results, networkConfig.symbol);
                this.showAlert('Transaksi selesai! Periksa hasil di bawah.', 'info');
                document.getElementById('resultsSection').style.display = 'block';
            } else {
                this.showAlert(data.error || 'Gagal mengirim transaksi.');
            }
        } catch (error) {
            console.error('Error sending transactions:', error);
            this.showAlert(error.message || 'Error mengirim transaksi.');
        } finally {
            this.hideLoading();
        }
    }

    displayResults(results, symbol) {
        const container = document.getElementById('resultsContainer');
        
        const successCount = results.filter(r => r.status === 'success').length;
        const failedCount = results.filter(r => r.status === 'failed').length;

        const summaryHtml = `
            <div class="alert alert-info mb-3">
                <h6 class="mb-2">Ringkasan Transaksi</h6>
                <p class="mb-0">
                    <strong>Total:</strong> ${results.length} transaksi |
                    <strong class="text-success">Berhasil:</strong> ${successCount} |
                    <strong class="text-danger">Gagal:</strong> ${failedCount}
                </p>
            </div>
        `;

        const resultsHtml = results.map((result, index) => `
            <div class="result-item ${result.status === 'success' ? 'result-success' : 'result-failed'}">
                <div class="result-wallet">
                    <small class="text-muted">#${index + 1}</small><br>
                    ${result.wallet}
                </div>
                <div class="result-details">
                    <div>
                        <span class="status-badge ${result.status === 'success' ? 'status-success' : 'status-failed'}">
                            ${result.status}
                        </span>
                    </div>
                    <div class="result-amount">
                        ${result.amount} ${symbol}
                    </div>
                    <div>
                        ${result.tx_hash ? 
                            `<a href="${result.explorer_url || '#'}" target="_blank" class="tx-hash-link">
                                <i class="fas fa-external-link-alt me-1"></i>
                                ${result.tx_hash.substring(0, 16)}...
                            </a>` : 
                            '<span class="text-muted">Tidak ada TX Hash</span>'
                        }
                    </div>
                </div>
                ${result.error ? `<div class="error-text mt-2">${result.error}</div>` : ''}
            </div>
        `).join('');

        container.innerHTML = summaryHtml + resultsHtml;
    }

    async clearSession() {
        const confirmed = confirm('Apakah Anda yakin ingin menghapus semua data dan mulai ulang?');
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch('/clear_session', {
                method: 'POST'
            });

            if (response.ok) {
                // Reset UI
                this.wallets = [];
                this.balances = [];
                this.selectedNetwork = null;

                document.getElementById('privateKeyFile').value = '';
                document.getElementById('networkSelect').value = '';
                document.getElementById('recipientAddress').value = '';
                document.querySelectorAll('input[name="percentage"]').forEach(radio => {
                    radio.checked = false;
                });

                document.getElementById('walletsList').style.display = 'none';
                document.getElementById('networkSection').style.display = 'none';
                document.getElementById('transferSection').style.display = 'none';
                document.getElementById('resultsSection').style.display = 'none';
                document.getElementById('customNetworkFields').style.display = 'none';

                this.showAlert('Sesi berhasil dibersihkan!', 'success');
            }
        } catch (error) {
            console.error('Error clearing session:', error);
            this.showAlert('Error membersihkan sesi.');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EVMMultiSender();
});
