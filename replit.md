# EVM Multi Sender

## Overview

EVM Multi Sender is a web application that enables users to send native cryptocurrency from multiple Ethereum Virtual Machine (EVM) compatible wallets simultaneously. The application provides a simple interface for importing private keys, selecting blockchain networks, checking balances, and executing batch transactions across multiple wallets. It supports various EVM networks including Ethereum Mainnet, Sepolia Testnet, Holesky Testnet, and Monad Testnet.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology Stack**: HTML5, CSS3, vanilla JavaScript with Bootstrap 5 for UI components
- **Design Pattern**: Single-page application (SPA) with component-based JavaScript class structure
- **UI Framework**: Bootstrap 5 with dark theme and Font Awesome icons for consistent styling
- **State Management**: Client-side state management using JavaScript class properties to track wallets, network selection, and balances

### Backend Architecture
- **Framework**: Flask web framework for Python
- **Architecture Pattern**: Simple MVC pattern with route handlers, service layer, and template rendering
- **Session Management**: Flask sessions with configurable secret key for maintaining user state
- **Middleware**: ProxyFix middleware for handling reverse proxy headers
- **Error Handling**: Try-catch blocks with JSON error responses for API endpoints

### Blockchain Integration
- **Web3 Library**: Web3.py for Ethereum blockchain interactions
- **Network Support**: Multi-network architecture supporting multiple EVM-compatible chains
- **Account Management**: Private key to wallet address derivation using Web3 account utilities
- **Transaction Processing**: Asynchronous transaction handling for batch operations

### File Processing
- **Upload Handling**: Server-side file upload processing for private key import
- **Data Validation**: Hex format validation for private keys with 0x prefix normalization
- **Security**: In-memory processing of sensitive private key data without persistent storage

## External Dependencies

### Blockchain Networks
- **Ethereum Mainnet**: Primary network via eth.llamarpc.com RPC endpoint
- **Sepolia Testnet**: Test network via rpc.sepolia.org for development
- **Holesky Testnet**: Alternative test network via ethereum-holesky.publicnode.com
- **Monad Testnet**: Specialized testnet via testnet-rpc.monad.xyz

### Third-Party Libraries
- **Web3.py**: Core blockchain interaction library for Ethereum compatibility
- **Flask**: Web framework for HTTP server and routing
- **Bootstrap 5**: Frontend CSS framework for responsive design
- **Font Awesome**: Icon library for user interface elements

### Development Tools
- **Werkzeug**: WSGI utilities including ProxyFix middleware
- **Python asyncio**: Asynchronous programming support for concurrent operations
- **aiohttp**: HTTP client library for asynchronous network requests

### Browser APIs
- **File API**: Client-side file reading for private key upload functionality
- **Fetch API**: AJAX requests for server communication
- **Bootstrap Modal**: UI components for loading states and user feedback