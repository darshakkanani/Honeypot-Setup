// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title HoneyPortLogger
 * @dev Smart contract for secure, immutable honeypot attack logging
 * @author HoneyPort Security Team
 */
contract HoneyPortLogger {
    
    // Events
    event AttackLogged(
        bytes32 indexed logHash,
        address indexed logger,
        uint256 timestamp,
        string attackType,
        string severity
    );
    
    event BlockMined(
        uint256 indexed blockNumber,
        bytes32 blockHash,
        uint256 logCount,
        uint256 timestamp
    );
    
    event VerificationRequested(
        bytes32 indexed logHash,
        address indexed verifier,
        uint256 timestamp
    );
    
    // Structs
    struct AttackLog {
        bytes32 logHash;
        string sourceIP;
        string attackType;
        string severity;
        string payload;
        string aiDecision;
        uint256 timestamp;
        address logger;
        bool verified;
    }
    
    struct LogBlock {
        uint256 blockNumber;
        bytes32 blockHash;
        bytes32 previousHash;
        uint256 timestamp;
        bytes32[] logHashes;
        uint256 nonce;
        address miner;
    }
    
    // State variables
    mapping(bytes32 => AttackLog) public attackLogs;
    mapping(uint256 => LogBlock) public logBlocks;
    mapping(address => bool) public authorizedLoggers;
    mapping(address => bool) public authorizedVerifiers;
    
    bytes32[] public allLogHashes;
    uint256 public currentBlockNumber;
    uint256 public constant BLOCK_SIZE = 100;
    uint256 public constant MINING_DIFFICULTY = 4;
    
    address public owner;
    bool public contractActive;
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier onlyAuthorizedLogger() {
        require(authorizedLoggers[msg.sender], "Not authorized to log attacks");
        _;
    }
    
    modifier onlyAuthorizedVerifier() {
        require(authorizedVerifiers[msg.sender], "Not authorized to verify logs");
        _;
    }
    
    modifier contractIsActive() {
        require(contractActive, "Contract is not active");
        _;
    }
    
    // Constructor
    constructor() {
        owner = msg.sender;
        authorizedLoggers[msg.sender] = true;
        authorizedVerifiers[msg.sender] = true;
        contractActive = true;
        currentBlockNumber = 0;
    }
    
    /**
     * @dev Log a new attack event to the blockchain
     * @param _sourceIP Source IP address of the attack
     * @param _attackType Type of attack (SQL injection, XSS, etc.)
     * @param _severity Attack severity level
     * @param _payload Attack payload data
     * @param _aiDecision AI decision made for this attack
     */
    function logAttack(
        string memory _sourceIP,
        string memory _attackType,
        string memory _severity,
        string memory _payload,
        string memory _aiDecision
    ) external onlyAuthorizedLogger contractIsActive returns (bytes32) {
        
        // Create unique hash for this log entry
        bytes32 logHash = keccak256(abi.encodePacked(
            _sourceIP,
            _attackType,
            _severity,
            _payload,
            _aiDecision,
            block.timestamp,
            msg.sender,
            allLogHashes.length
        ));
        
        // Ensure log doesn't already exist
        require(attackLogs[logHash].timestamp == 0, "Log already exists");
        
        // Create attack log
        attackLogs[logHash] = AttackLog({
            logHash: logHash,
            sourceIP: _sourceIP,
            attackType: _attackType,
            severity: _severity,
            payload: _payload,
            aiDecision: _aiDecision,
            timestamp: block.timestamp,
            logger: msg.sender,
            verified: false
        });
        
        // Add to global log list
        allLogHashes.push(logHash);
        
        // Emit event
        emit AttackLogged(logHash, msg.sender, block.timestamp, _attackType, _severity);
        
        // Check if we need to mine a new block
        if (allLogHashes.length % BLOCK_SIZE == 0) {
            _mineBlock();
        }
        
        return logHash;
    }
    
    /**
     * @dev Mine a new block with accumulated logs
     */
    function _mineBlock() internal {
        uint256 startIndex = currentBlockNumber * BLOCK_SIZE;
        uint256 endIndex = startIndex + BLOCK_SIZE;
        
        // Ensure we have enough logs
        if (endIndex > allLogHashes.length) {
            endIndex = allLogHashes.length;
        }
        
        // Create array of log hashes for this block
        bytes32[] memory blockLogs = new bytes32[](endIndex - startIndex);
        for (uint256 i = startIndex; i < endIndex; i++) {
            blockLogs[i - startIndex] = allLogHashes[i];
        }
        
        // Get previous block hash
        bytes32 previousHash = currentBlockNumber > 0 ? 
            logBlocks[currentBlockNumber - 1].blockHash : 
            bytes32(0);
        
        // Mine block with proof of work
        (bytes32 blockHash, uint256 nonce) = _proofOfWork(previousHash, blockLogs);
        
        // Create new block
        logBlocks[currentBlockNumber] = LogBlock({
            blockNumber: currentBlockNumber,
            blockHash: blockHash,
            previousHash: previousHash,
            timestamp: block.timestamp,
            logHashes: blockLogs,
            nonce: nonce,
            miner: msg.sender
        });
        
        // Emit block mined event
        emit BlockMined(currentBlockNumber, blockHash, blockLogs.length, block.timestamp);
        
        // Increment block number
        currentBlockNumber++;
    }
    
    /**
     * @dev Proof of work mining algorithm
     * @param _previousHash Hash of previous block
     * @param _logHashes Array of log hashes to include in block
     */
    function _proofOfWork(
        bytes32 _previousHash, 
        bytes32[] memory _logHashes
    ) internal view returns (bytes32, uint256) {
        
        uint256 nonce = 0;
        bytes32 hash;
        
        // Create target (difficulty)
        bytes32 target = bytes32(2**(256 - MINING_DIFFICULTY) - 1);
        
        while (true) {
            hash = keccak256(abi.encodePacked(
                _previousHash,
                _logHashes,
                block.timestamp,
                nonce
            ));
            
            if (hash <= target) {
                break;
            }
            
            nonce++;
            
            // Prevent infinite loop in case of issues
            if (nonce > 1000000) {
                break;
            }
        }
        
        return (hash, nonce);
    }
    
    /**
     * @dev Verify the integrity of a specific log
     * @param _logHash Hash of the log to verify
     */
    function verifyLog(bytes32 _logHash) external onlyAuthorizedVerifier returns (bool) {
        require(attackLogs[_logHash].timestamp != 0, "Log does not exist");
        
        AttackLog memory log = attackLogs[_logHash];
        
        // Recreate hash to verify integrity
        bytes32 calculatedHash = keccak256(abi.encodePacked(
            log.sourceIP,
            log.attackType,
            log.severity,
            log.payload,
            log.aiDecision,
            log.timestamp,
            log.logger,
            _getLogIndex(_logHash)
        ));
        
        bool isValid = (calculatedHash == _logHash);
        
        if (isValid) {
            attackLogs[_logHash].verified = true;
        }
        
        emit VerificationRequested(_logHash, msg.sender, block.timestamp);
        
        return isValid;
    }
    
    /**
     * @dev Verify the integrity of the entire blockchain
     */
    function verifyBlockchain() external view returns (bool) {
        for (uint256 i = 1; i < currentBlockNumber; i++) {
            LogBlock memory currentBlock = logBlocks[i];
            LogBlock memory previousBlock = logBlocks[i - 1];
            
            // Verify previous hash link
            if (currentBlock.previousHash != previousBlock.blockHash) {
                return false;
            }
            
            // Verify block hash
            bytes32 calculatedHash = keccak256(abi.encodePacked(
                currentBlock.previousHash,
                currentBlock.logHashes,
                currentBlock.timestamp,
                currentBlock.nonce
            ));
            
            if (calculatedHash != currentBlock.blockHash) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * @dev Get attack log details
     * @param _logHash Hash of the log to retrieve
     */
    function getAttackLog(bytes32 _logHash) external view returns (
        string memory sourceIP,
        string memory attackType,
        string memory severity,
        string memory payload,
        string memory aiDecision,
        uint256 timestamp,
        address logger,
        bool verified
    ) {
        AttackLog memory log = attackLogs[_logHash];
        require(log.timestamp != 0, "Log does not exist");
        
        return (
            log.sourceIP,
            log.attackType,
            log.severity,
            log.payload,
            log.aiDecision,
            log.timestamp,
            log.logger,
            log.verified
        );
    }
    
    /**
     * @dev Get block details
     * @param _blockNumber Block number to retrieve
     */
    function getBlock(uint256 _blockNumber) external view returns (
        bytes32 blockHash,
        bytes32 previousHash,
        uint256 timestamp,
        bytes32[] memory logHashes,
        uint256 nonce,
        address miner
    ) {
        require(_blockNumber < currentBlockNumber, "Block does not exist");
        
        LogBlock memory logBlock = logBlocks[_blockNumber];
        
        return (
            logBlock.blockHash,
            logBlock.previousHash,
            logBlock.timestamp,
            logBlock.logHashes,
            logBlock.nonce,
            logBlock.miner
        );
    }
    
    /**
     * @dev Get total number of logs
     */
    function getTotalLogs() external view returns (uint256) {
        return allLogHashes.length;
    }
    
    /**
     * @dev Get recent logs
     * @param _count Number of recent logs to retrieve
     */
    function getRecentLogs(uint256 _count) external view returns (bytes32[] memory) {
        uint256 totalLogs = allLogHashes.length;
        
        if (_count > totalLogs) {
            _count = totalLogs;
        }
        
        bytes32[] memory recentLogs = new bytes32[](_count);
        
        for (uint256 i = 0; i < _count; i++) {
            recentLogs[i] = allLogHashes[totalLogs - 1 - i];
        }
        
        return recentLogs;
    }
    
    /**
     * @dev Add authorized logger
     * @param _logger Address to authorize for logging
     */
    function addAuthorizedLogger(address _logger) external onlyOwner {
        authorizedLoggers[_logger] = true;
    }
    
    /**
     * @dev Remove authorized logger
     * @param _logger Address to remove from logging authorization
     */
    function removeAuthorizedLogger(address _logger) external onlyOwner {
        authorizedLoggers[_logger] = false;
    }
    
    /**
     * @dev Add authorized verifier
     * @param _verifier Address to authorize for verification
     */
    function addAuthorizedVerifier(address _verifier) external onlyOwner {
        authorizedVerifiers[_verifier] = true;
    }
    
    /**
     * @dev Emergency pause contract
     */
    function pauseContract() external onlyOwner {
        contractActive = false;
    }
    
    /**
     * @dev Resume contract operations
     */
    function resumeContract() external onlyOwner {
        contractActive = true;
    }
    
    /**
     * @dev Get index of a log hash in the global array
     * @param _logHash Hash to find index for
     */
    function _getLogIndex(bytes32 _logHash) internal view returns (uint256) {
        for (uint256 i = 0; i < allLogHashes.length; i++) {
            if (allLogHashes[i] == _logHash) {
                return i;
            }
        }
        revert("Log hash not found");
    }
    
    /**
     * @dev Get contract statistics
     */
    function getContractStats() external view returns (
        uint256 totalLogs,
        uint256 totalBlocks,
        uint256 verifiedLogs,
        bool isActive
    ) {
        uint256 verified = 0;
        for (uint256 i = 0; i < allLogHashes.length; i++) {
            if (attackLogs[allLogHashes[i]].verified) {
                verified++;
            }
        }
        
        return (
            allLogHashes.length,
            currentBlockNumber,
            verified,
            contractActive
        );
    }
}
