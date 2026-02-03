# Memory Optimization Fix for Render Deployment

## Problem
When analyzing 15+ emails, the Render worker was getting killed with `SIGKILL! Perhaps out of memory?` error. The frontend showed JSON parsing errors because the server was returning HTML error pages instead of JSON responses.

## Root Causes
1. **Memory Exhaustion**: Processing all emails at once with OCR consumed too much RAM
2. **Large Payloads**: Email payload data was being stored in memory unnecessarily
3. **Poor Garbage Collection**: Python wasn't releasing memory between operations
4. **Session Bloat**: Storing full email bodies and large data structures in sessions
5. **Frontend Error Handling**: Not detecting HTML error pages before trying to parse as JSON

## Solutions Implemented

### 1. Batch Processing (app.py)
- Process emails in batches of 5 instead of all at once
- Force garbage collection between batches
- Reduces peak memory usage significantly

```python
BATCH_SIZE = 5  # Process 5 emails at a time
for i in range(0, len(emails), BATCH_SIZE):
    batch = emails[i:i + BATCH_SIZE]
    # Process batch...
    del batch
    gc.collect()
```

### 2. Memory Cleanup (analyzer.py)
- Remove large `payload` data after processing each email
- Add garbage collection after image OCR processing
- Force GC at the end of analyze_emails()

```python
# Remove payload after processing
if 'payload' in email:
    del email['payload']

# After OCR
del image_result
gc.collect()
```

### 3. Session Size Reduction (app.py)
- Remove email bodies from session storage
- Limit image offers to top 5 per email
- Only store first 10 normal emails
- Clean data before storing in session

```python
def clean_email_data(email):
    cleaned = email.copy()
    if 'body' in cleaned:
        del cleaned['body']
    if 'image_offers' in cleaned and len(cleaned['image_offers']) > 5:
        cleaned['image_offers'] = cleaned['image_offers'][:5]
    return cleaned
```

### 4. Frontend Error Handling (dashboard.html)
- Check response content-type before parsing JSON
- Display user-friendly error message for server crashes
- Prevents "Unexpected token '<'" error

```javascript
const contentType = response.headers.get('content-type');
if (!contentType || !contentType.includes('application/json')) {
    throw new Error('Server error: The server may be out of memory. Try analyzing fewer emails.');
}
```

### 5. Gunicorn Configuration (render.yaml)
Optimized worker settings for low-memory environments:
- **Timeout**: Increased to 300s for large analysis jobs
- **Worker restart**: `--max-requests 100` to prevent memory leaks
- **Temp directory**: `--worker-tmp-dir /dev/shm` (RAM disk for better performance)
- **Worker class**: `sync` for better memory control

```yaml
startCommand: "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300 --workers 1 --worker-class sync --max-requests 100 --max-requests-jitter 10 --worker-tmp-dir /dev/shm"
```

## Expected Improvements

### Memory Usage
- **Before**: ~500MB+ for 15 emails (caused OOM on 512MB instances)
- **After**: ~200-300MB for 15 emails (fits comfortably in 512MB)

### Scalability
- ✅ Can now analyze 15-20 emails reliably
- ✅ OCR processing distributed across batches
- ✅ Memory released progressively

### Error Handling
- ✅ Graceful error messages instead of JSON parse errors
- ✅ MemoryError exceptions caught and reported
- ✅ Server errors detected before JSON parsing

## Testing Recommendations

1. **Test with 10 emails**: Should work smoothly (baseline)
2. **Test with 15 emails**: Should now complete without OOM
3. **Test with 20 emails**: Monitor memory usage
4. **Test OCR-heavy emails**: Emails with many images

## Deployment Steps

1. Commit all changes:
```bash
git add app.py analyzer.py render.yaml templates/dashboard.html
git commit -m "Fix memory issues for 15+ email analysis"
git push
```

2. Render will automatically deploy the changes

3. Monitor logs for:
   - Batch processing messages
   - Memory cleanup confirmations
   - No more SIGKILL errors

## Monitoring

Watch for these log messages:
- ✅ `Processing batch X/Y (5 emails)...`
- ✅ `Batch X complete. Memory released.`
- ✅ `Analysis complete. Stored N result categories`

## Future Optimizations (if needed)

If still experiencing issues with 20+ emails:

1. **Reduce batch size**: Change `BATCH_SIZE = 5` to `BATCH_SIZE = 3`
2. **Disable OCR for some categories**: Only run OCR on coupons/gift cards
3. **Upgrade Render plan**: Move to 1GB RAM instance
4. **Add progress streaming**: Return results progressively via WebSocket

## Notes

- The 5-email batch size is a balance between performance and memory
- Smaller batches = slower but safer
- Larger batches = faster but more memory
- Current setting should work for Render's 512MB free tier
