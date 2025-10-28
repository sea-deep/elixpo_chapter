/**
 * A per-user, per-command rate limiter using sliding window algorithm
 */
class RateLimiter {
    constructor() {
        // Store command usage in format: userId_commandName -> [{timestamp}]
        this.usageMap = new Map();
        
        // Default limits (can be configured)
        this.limits = {
            generate: { window: 60, maxRequests: 5 },  // 5 requests per minute
            remix: { window: 60, maxRequests: 5 },     // 5 requests per minute
            help: { window: 30, maxRequests: 3 },      // 3 requests per 30 seconds
            ping: { window: 10, maxRequests: 2 }       // 2 requests per 10 seconds
        };
        
        // Clean up old entries every 5 minutes
        setInterval(() => this.cleanup(), 5 * 60 * 1000);
    }
    
    /**
     * Check if a user has exceeded their rate limit for a command
     * @param {string} userId The Discord user ID
     * @param {string} commandName The command being used
     * @returns {boolean} True if rate limited, false otherwise
     */
    isRateLimited(userId, commandName) {
        const key = `${userId}_${commandName}`;
        const now = Date.now();
        
        // Get command limits
        const limit = this.limits[commandName];
        if (!limit) return false; // No limit for this command
        
        // Get user's command usage
        let usage = this.usageMap.get(key) || [];
        
        // Remove timestamps outside the window
        usage = usage.filter(timestamp => 
            now - timestamp < limit.window * 1000
        );
        
        // Update usage
        this.usageMap.set(key, usage);
        
        // Check if user has exceeded limit
        if (usage.length >= limit.maxRequests) {
            return true;
        }
        
        // Add current usage
        usage.push(now);
        return false;
    }
    
    /**
     * Get remaining cooldown time in seconds
     * @param {string} userId The Discord user ID
     * @param {string} commandName The command being used
     * @returns {number} Seconds until next allowed request, or 0 if not rate limited
     */
    getRemainingCooldown(userId, commandName) {
        const key = `${userId}_${commandName}`;
        const now = Date.now();
        
        const limit = this.limits[commandName];
        if (!limit) return 0;
        
        const usage = this.usageMap.get(key);
        if (!usage || usage.length === 0) return 0;
        
        // If not at limit, no cooldown
        if (usage.length < limit.maxRequests) return 0;
        
        // Get oldest timestamp in window
        const oldestInWindow = usage[0];
        const cooldownEnds = oldestInWindow + (limit.window * 1000);
        
        return Math.max(0, Math.ceil((cooldownEnds - now) / 1000));
    }
    
    /**
     * Clean up old entries to prevent memory leaks
     */
    cleanup() {
        const now = Date.now();
        for (const [key, timestamps] of this.usageMap.entries()) {
            // Find the applicable limit window
            const commandName = key.split('_')[1];
            const limit = this.limits[commandName];
            if (!limit) continue;
            
            // Remove entries older than the window
            const validTimestamps = timestamps.filter(
                timestamp => now - timestamp < limit.window * 1000
            );
            
            if (validTimestamps.length === 0) {
                this.usageMap.delete(key);
            } else {
                this.usageMap.set(key, validTimestamps);
            }
        }
    }
}

export const rateLimiter = new RateLimiter();