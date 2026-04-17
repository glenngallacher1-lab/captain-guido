// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Captain Guido Token ($GUIDO)
 * @notice ERC-20 with automatic burn and treasury fee on every transfer.
 *
 * ── TOKENOMICS (FINALIZE BEFORE DEPLOY) ──────────────────────────────────────
 *   TOTAL_SUPPLY   1,000,000,000  GUIDO       ← adjust
 *   TREASURY_FEE   2%  per transfer            ← adjust (basis points: 200)
 *   BURN_FEE       1%  per transfer            ← adjust (basis points: 100)
 *   MAX_TOTAL_FEE  10% hard cap (safety)
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Compile with: solc ^0.8.20
 * Recommended deploy target: Ethereum mainnet or any EVM-compatible chain.
 * Requires OpenZeppelin Contracts v5:
 *   npm install @openzeppelin/contracts
 */

// ── Minimal OpenZeppelin interfaces (inline so the file is self-contained) ──
// If you are using Hardhat/Foundry with OZ installed, replace these with:
//   import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
//   import "@openzeppelin/contracts/access/Ownable.sol";
// and remove the abstract contracts below.

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }
}

abstract contract Ownable is Context {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error OwnableUnauthorizedAccount(address account);
    error OwnableInvalidOwner(address owner);

    constructor(address initialOwner) {
        if (initialOwner == address(0)) revert OwnableInvalidOwner(address(0));
        _transferOwnership(initialOwner);
    }

    modifier onlyOwner() {
        _checkOwner();
        _;
    }

    function owner() public view virtual returns (address) { return _owner; }

    function _checkOwner() internal view virtual {
        if (_owner != _msgSender()) revert OwnableUnauthorizedAccount(_msgSender());
    }

    function renounceOwnership() public virtual onlyOwner {
        _transferOwnership(address(0));
    }

    function transferOwnership(address newOwner) public virtual onlyOwner {
        if (newOwner == address(0)) revert OwnableInvalidOwner(address(0));
        _transferOwnership(newOwner);
    }

    function _transferOwnership(address newOwner) internal virtual {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}

interface IERC20 {
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

interface IERC20Metadata is IERC20 {
    function name()     external view returns (string memory);
    function symbol()   external view returns (string memory);
    function decimals() external view returns (uint8);
}

// ── ERC-20 base ───────────────────────────────────────────────────────────────
contract ERC20 is Context, IERC20, IERC20Metadata {
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    uint256 private _totalSupply;
    string  private _name;
    string  private _symbol;

    constructor(string memory name_, string memory symbol_) {
        _name   = name_;
        _symbol = symbol_;
    }

    function name()     public view virtual override returns (string memory) { return _name; }
    function symbol()   public view virtual override returns (string memory) { return _symbol; }
    function decimals() public view virtual override returns (uint8)         { return 18; }
    function totalSupply() public view virtual override returns (uint256)    { return _totalSupply; }
    function balanceOf(address account) public view virtual override returns (uint256) { return _balances[account]; }

    function transfer(address to, uint256 amount) public virtual override returns (bool) {
        _transfer(_msgSender(), to, amount);
        return true;
    }

    function allowance(address owner, address spender) public view virtual override returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(address spender, uint256 amount) public virtual override returns (bool) {
        _approve(_msgSender(), spender, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) public virtual override returns (bool) {
        address spender = _msgSender();
        _spendAllowance(from, spender, amount);
        _transfer(from, to, amount);
        return true;
    }

    function _transfer(address from, address to, uint256 amount) internal virtual {
        require(from != address(0), "ERC20: transfer from zero address");
        require(to   != address(0), "ERC20: transfer to zero address");
        uint256 fromBalance = _balances[from];
        require(fromBalance >= amount, "ERC20: transfer amount exceeds balance");
        unchecked { _balances[from] = fromBalance - amount; }
        _balances[to] += amount;
        emit Transfer(from, to, amount);
    }

    function _mint(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: mint to zero address");
        _totalSupply    += amount;
        _balances[account] += amount;
        emit Transfer(address(0), account, amount);
    }

    function _burn(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: burn from zero address");
        uint256 accountBalance = _balances[account];
        require(accountBalance >= amount, "ERC20: burn amount exceeds balance");
        unchecked { _balances[account] = accountBalance - amount; }
        _totalSupply -= amount;
        emit Transfer(account, address(0), amount);
    }

    function _approve(address owner, address spender, uint256 amount) internal virtual {
        require(owner   != address(0), "ERC20: approve from zero address");
        require(spender != address(0), "ERC20: approve to zero address");
        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }

    function _spendAllowance(address owner, address spender, uint256 amount) internal virtual {
        uint256 currentAllowance = allowance(owner, spender);
        if (currentAllowance != type(uint256).max) {
            require(currentAllowance >= amount, "ERC20: insufficient allowance");
            unchecked { _approve(owner, spender, currentAllowance - amount); }
        }
    }
}

// ═════════════════════════════════════════════════════════════════════════════
//  Captain Guido Token
// ═════════════════════════════════════════════════════════════════════════════
contract CaptainGuidoToken is ERC20, Ownable {

    // ── Constants ────────────────────────────────────────────────────────────
    /// @dev Basis points denominator (100% = 10_000 bp)
    uint256 public constant BPS = 10_000;
    /// @dev Hard cap: combined fee can never exceed 10%
    uint256 public constant MAX_TOTAL_FEE_BPS = 1_000;

    // ── Tokenomics (FINALIZE BEFORE DEPLOY) ─────────────────────────────────
    /// @notice Total supply minted at construction. 1 billion GUIDO.
    uint256 public constant TOTAL_SUPPLY = 1_000_000_000 * 10 ** 18; // ← ADJUST

    // ── Fee state ────────────────────────────────────────────────────────────
    /// @notice Basis points sent to treasury on each transfer (default 2%).
    uint256 public treasuryFeeBps = 200; // ← ADJUST

    /// @notice Basis points burned on each transfer (default 1%).
    uint256 public burnFeeBps = 100;     // ← ADJUST

    /// @notice Wallet that receives the treasury cut.
    address public treasury;

    // ── Fee exclusions ───────────────────────────────────────────────────────
    /// @notice Addresses excluded from both fees (owner, treasury, presale contract, etc.)
    mapping(address => bool) public isExcludedFromFee;

    // ── Events ───────────────────────────────────────────────────────────────
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);
    event FeesUpdated(uint256 treasuryFeeBps, uint256 burnFeeBps);
    event ExclusionUpdated(address indexed account, bool excluded);
    event ManualBurn(address indexed from, uint256 amount);

    // ── Errors ───────────────────────────────────────────────────────────────
    error ZeroAddress();
    error FeeTooHigh(uint256 combined, uint256 max);
    error BurnExceedsBalance();

    // ── Constructor ──────────────────────────────────────────────────────────
    /**
     * @param _treasury  Wallet to receive treasury fees.
     *                   Set to deployer address if not finalised yet.
     */
    constructor(address _treasury)
        ERC20("Captain Guido Token", "GUIDO")
        Ownable(msg.sender)
    {
        if (_treasury == address(0)) revert ZeroAddress();
        treasury = _treasury;

        // Exclude deployer and treasury from fees
        isExcludedFromFee[msg.sender] = true;
        isExcludedFromFee[_treasury]  = true;
        // Dead address always excluded
        isExcludedFromFee[address(0xdead)] = true;

        // Mint entire supply to deployer for distribution
        _mint(msg.sender, TOTAL_SUPPLY);
    }

    // ── Transfer override ────────────────────────────────────────────────────
    /**
     * @dev Overrides ERC-20 _transfer to deduct treasury fee and burn fee.
     *      Fee-excluded addresses (owner, treasury, presale contract) bypass fees.
     */
    function _transfer(address from, address to, uint256 amount) internal override {
        require(from != address(0), "ERC20: transfer from zero address");
        require(to   != address(0), "ERC20: transfer to zero address");

        if (isExcludedFromFee[from] || isExcludedFromFee[to]) {
            // No fee path
            super._transfer(from, to, amount);
            return;
        }

        uint256 treasuryAmt = (amount * treasuryFeeBps) / BPS;
        uint256 burnAmt     = (amount * burnFeeBps)     / BPS;
        uint256 sendAmt     = amount - treasuryAmt - burnAmt;

        // Send treasury cut
        if (treasuryAmt > 0) {
            super._transfer(from, treasury, treasuryAmt);
        }

        // Burn cut (reduces total supply)
        if (burnAmt > 0) {
            _burn(from, burnAmt);
        }

        // Deliver remainder
        super._transfer(from, to, sendAmt);
    }

    // ── Owner: fee management ────────────────────────────────────────────────
    /**
     * @notice Update fee rates. Combined fee cannot exceed MAX_TOTAL_FEE_BPS (10%).
     * @param _treasuryBps  New treasury fee in basis points.
     * @param _burnBps      New burn fee in basis points.
     */
    function setFees(uint256 _treasuryBps, uint256 _burnBps) external onlyOwner {
        uint256 combined = _treasuryBps + _burnBps;
        if (combined > MAX_TOTAL_FEE_BPS) revert FeeTooHigh(combined, MAX_TOTAL_FEE_BPS);
        treasuryFeeBps = _treasuryBps;
        burnFeeBps     = _burnBps;
        emit FeesUpdated(_treasuryBps, _burnBps);
    }

    /**
     * @notice Set treasury wallet address.
     * @param _treasury New treasury wallet.
     */
    function setTreasury(address _treasury) external onlyOwner {
        if (_treasury == address(0)) revert ZeroAddress();
        address old = treasury;
        // Update fee exclusion mappings
        isExcludedFromFee[old]      = false;
        isExcludedFromFee[_treasury] = true;
        treasury = _treasury;
        emit TreasuryUpdated(old, _treasury);
    }

    // ── Owner: exclusion management ──────────────────────────────────────────
    /**
     * @notice Exclude or include an address from transfer fees.
     *         Use for presale contract, liquidity pool router, CEX wallets, etc.
     */
    function setExcludedFromFee(address account, bool excluded) external onlyOwner {
        if (account == address(0)) revert ZeroAddress();
        isExcludedFromFee[account] = excluded;
        emit ExclusionUpdated(account, excluded);
    }

    // ── Manual burn ──────────────────────────────────────────────────────────
    /**
     * @notice Any holder can manually burn their own tokens.
     * @param amount Amount to burn (in token wei, i.e. amount * 10**18).
     */
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
        emit ManualBurn(msg.sender, amount);
    }

    // ── View helpers ─────────────────────────────────────────────────────────
    /**
     * @notice Returns the effective fee-inclusive cost for sending `amount` tokens.
     *         Useful for front-end presale calculators.
     */
    function feesFor(uint256 amount)
        external
        view
        returns (uint256 treasuryAmt, uint256 burnAmt, uint256 receiverAmt)
    {
        treasuryAmt = (amount * treasuryFeeBps) / BPS;
        burnAmt     = (amount * burnFeeBps)     / BPS;
        receiverAmt = amount - treasuryAmt - burnAmt;
    }

    /**
     * @notice Circulating supply = totalSupply (burn reduces this automatically).
     */
    function circulatingSupply() external view returns (uint256) {
        return totalSupply();
    }
}
