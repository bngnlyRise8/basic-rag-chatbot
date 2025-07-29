import { writable } from 'svelte/store';

export interface Message {
	id: string;
	role: 'user' | 'llm';
	content: string;
	created_at: string;
}

export interface Conversation {
	id: string;
	title?: string;
	created_at: string;
	updated_at: string;
	messages: Message[];
}

export const currentConversation = writable<Conversation | null>(null);
export const conversations = writable<Conversation[]>([]);
export const isLoading = writable(false);

const API_BASE = 'http://localhost:8000/api';

export async function sendMessage(question: string, conversationId?: string) {
	isLoading.set(true);
	
	try {
		const response = await fetch(`${API_BASE}/prompt`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				question,
				conversation_id: conversationId
			})
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const data = await response.json();
		return data;
	} catch (error) {
		console.error('Error sending message:', error);
		throw error;
	} finally {
		isLoading.set(false);
	}
}

export async function uploadDocument(file: File) {
	const formData = new FormData();
	formData.append('file', file);

	try {
		const response = await fetch(`${API_BASE}/document`, {
			method: 'POST',
			body: formData
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.detail || 'Upload failed');
		}

		return await response.json();
	} catch (error) {
		console.error('Upload error:', error);
		throw error;
	}
}

export function createNewConversation() {
	currentConversation.set({
		id: crypto.randomUUID(),
		created_at: new Date().toISOString(),
		updated_at: new Date().toISOString(),
		messages: []
	});
}

export function addMessageToConversation(message: Message) {
	currentConversation.update(conv => {
		if (!conv) return conv;
		
		return {
			...conv,
			messages: [...conv.messages, message],
			updated_at: new Date().toISOString()
		};
	});
}