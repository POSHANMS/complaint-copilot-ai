# SSE streaming helper placeholder
async def stream_extraction_progress(state_updates):
    for update in state_updates:
        yield f"data: {update}\n\n"
