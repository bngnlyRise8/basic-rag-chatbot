<script lang="ts">
	import { onMount } from 'svelte';

	interface Message {
		id: string;
		role: 'user' | 'llm';
		content: string;
		created_at: string;
	}

	interface PromptResponse {
		question: string;
		answer: string;
		conversation_id: string;
	}

	let messages: Message[] = [];
	let inputMessage = '';
	let conversationId: string | null = null;
	let isLoading = false;
	let messagesContainer: HTMLElement;

	const API_BASE = 'http://localhost:8000/api';

	async function sendMessage() {
		if (!inputMessage.trim() || isLoading) return;

		const userMessage = inputMessage.trim();
		inputMessage = '';
		isLoading = true;

		messages = [...messages, {
			id: Date.now().toString(),
			role: 'user',
			content: userMessage,
			created_at: new Date().toISOString()
		}];

		scrollToBottom();

		try {
			const response = await fetch(`${API_BASE}/prompt`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					question: userMessage,
					conversation_id: conversationId
				})
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const data: PromptResponse = await response.json();
			conversationId = data.conversation_id;

			messages = [...messages, {
				id: (Date.now() + 1).toString(),
				role: 'llm',
				content: data.answer,
				created_at: new Date().toISOString()
			}];

			scrollToBottom();
		} catch (error) {
			console.error('Error sending message:', error);
			messages = [...messages, {
				id: (Date.now() + 1).toString(),
				role: 'llm',
				content: 'Sorry, I encountered an error processing your message.',
				created_at: new Date().toISOString()
			}];
		} finally {
			isLoading = false;
		}
	}

	function scrollToBottom() {
		setTimeout(() => {
			if (messagesContainer) {
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}
		}, 10);
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}

	function formatTime(isoString: string): string {
		return new Date(isoString).toLocaleTimeString([], { 
			hour: '2-digit', 
			minute: '2-digit' 
		});
	}

	function startNewConversation() {
		messages = [];
		conversationId = null;
	}
</script>

<div class="chat-container">
	<div class="chat-header">
		<h2>AI Chatbot</h2>
		<button on:click={startNewConversation} class="new-chat-btn">
			New Chat
		</button>
	</div>

	<div class="messages-container" bind:this={messagesContainer}>
		{#each messages as message (message.id)}
			<div class="message {message.role}">
				<div class="message-content">
					<div class="message-text">{message.content}</div>
					<div class="message-time">{formatTime(message.created_at)}</div>
				</div>
			</div>
		{/each}
		
		{#if isLoading}
			<div class="message llm">
				<div class="message-content">
					<div class="typing-indicator">
						<span></span>
						<span></span>
						<span></span>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="input-container">
		<textarea
			bind:value={inputMessage}
			on:keydown={handleKeyPress}
			placeholder="Ask a question about your documents..."
			disabled={isLoading}
			rows="1"
		></textarea>
		<button on:click={sendMessage} disabled={!inputMessage.trim() || isLoading}>
			Send
		</button>
	</div>
</div>

<style>
	.chat-container {
		display: flex;
		flex-direction: column;
		height: 100vh;
		max-width: 800px;
		margin: 0 auto;
		border: 1px solid #ddd;
		border-radius: 8px;
		overflow: hidden;
	}

	.chat-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: #f8f9fa;
		border-bottom: 1px solid #ddd;
	}

	.chat-header h2 {
		margin: 0;
		color: #333;
	}

	.new-chat-btn {
		padding: 0.5rem 1rem;
		background: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.new-chat-btn:hover {
		background: #0056b3;
	}

	.messages-container {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
		background: #fff;
	}

	.message {
		margin-bottom: 1rem;
		display: flex;
	}

	.message.user {
		justify-content: flex-end;
	}

	.message.llm {
		justify-content: flex-start;
	}

	.message-content {
		max-width: 70%;
		padding: 0.75rem 1rem;
		border-radius: 18px;
		position: relative;
	}

	.message.user .message-content {
		background: #007bff;
		color: white;
	}

	.message.llm .message-content {
		background: #f1f3f4;
		color: #333;
	}

	.message-text {
		word-wrap: break-word;
		white-space: pre-wrap;
	}

	.message-time {
		font-size: 0.75rem;
		opacity: 0.7;
		margin-top: 0.25rem;
	}

	.typing-indicator {
		display: flex;
		gap: 4px;
		align-items: center;
	}

	.typing-indicator span {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #666;
		animation: typing 1.4s infinite;
	}

	.typing-indicator span:nth-child(2) {
		animation-delay: 0.2s;
	}

	.typing-indicator span:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes typing {
		0%, 60%, 100% {
			transform: translateY(0);
		}
		30% {
			transform: translateY(-10px);
		}
	}

	.input-container {
		display: flex;
		padding: 1rem;
		border-top: 1px solid #ddd;
		background: #f8f9fa;
	}

	textarea {
		flex: 1;
		padding: 0.75rem;
		border: 1px solid #ddd;
		border-radius: 20px;
		resize: none;
		font-family: inherit;
		font-size: 1rem;
		min-height: 44px;
		max-height: 120px;
	}

	textarea:focus {
		outline: none;
		border-color: #007bff;
	}

	button {
		margin-left: 0.5rem;
		padding: 0.75rem 1.5rem;
		background: #007bff;
		color: white;
		border: none;
		border-radius: 20px;
		cursor: pointer;
		font-size: 1rem;
	}

	button:hover:not(:disabled) {
		background: #0056b3;
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>