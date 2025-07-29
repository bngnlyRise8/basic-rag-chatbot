<script lang="ts">
	import { onMount } from 'svelte';

	interface DocumentInfo {
		filename: string;
		file_hash: string;
	}

	interface DocumentListResponse {
		documents: DocumentInfo[];
	}

	let documents: DocumentInfo[] = [];
	let loading = true;
	let deleting: Set<string> = new Set();
	let error = '';

	const API_BASE = 'http://localhost:8000/api';

	async function loadDocuments() {
		loading = true;
		error = '';
		
		try {
			const response = await fetch(`${API_BASE}/documents`);
			
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const data: DocumentListResponse = await response.json();
			documents = data.documents;
		} catch (err) {
			console.error('Error loading documents:', err);
			error = 'Failed to load documents';
		} finally {
			loading = false;
		}
	}

	async function deleteDocument(file_hash: string, filename: string) {
		if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
			return;
		}

		deleting.add(file_hash);
		deleting = deleting; // Trigger reactivity

		try {
			const response = await fetch(`${API_BASE}/document/${encodeURIComponent(file_hash)}`, {
				method: 'DELETE'
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Delete failed');
			}

			const data = await response.json();
			console.log('Delete result:', data);

			// Refresh the document list from server to ensure consistency
			await loadDocuments();
		} catch (err) {
			console.error('Error deleting document:', err);
			error = `Failed to delete ${filename}: ${err instanceof Error ? err.message : 'Unknown error'}`;
		} finally {
			deleting.delete(file_hash);
			deleting = deleting; // Trigger reactivity
		}
	}

	onMount(() => {
		loadDocuments();
	});

	// Expose loadDocuments for parent component
	export { loadDocuments };
</script>

<div class="document-manager">
	<div class="header">
		<h3>Uploaded Documents</h3>
		<button on:click={loadDocuments} class="refresh-btn" disabled={loading}>
			{loading ? 'Loading...' : 'Refresh'}
		</button>
	</div>

	{#if error}
		<div class="error">
			{error}
			<button on:click={() => error = ''} class="close-error">×</button>
		</div>
	{/if}

	{#if loading}
		<div class="loading">Loading documents...</div>
	{:else if documents.length === 0}
		<div class="empty">
			No documents uploaded yet. Upload a PDF to get started!
		</div>
	{:else}
		<div class="document-list">
			{#each documents as doc (doc.file_hash)}
				<div class="document-item">
					<div class="document-info">
						<div class="filename">{doc.filename}</div>
						<div class="hash">Hash: {doc.file_hash.substring(0, 12)}...</div>
					</div>
					<button 
						on:click={() => deleteDocument(doc.file_hash, doc.filename)}
						class="delete-btn"
						disabled={deleting.has(doc.file_hash)}
					>
						{deleting.has(doc.file_hash) ? 'Deleting...' : 'Delete'}
					</button>
				</div>
			{/each}
		</div>

		<div class="summary">
			Total: {documents.length} document{documents.length !== 1 ? 's' : ''}
		</div>
	{/if}
</div>

<style>
	.document-manager {
		background: white;
		border: 1px solid #ddd;
		border-radius: 8px;
		padding: 1rem;
		margin-bottom: 1rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.header h3 {
		margin: 0;
		color: #333;
	}

	.refresh-btn {
		padding: 0.5rem 1rem;
		background: #6c757d;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.refresh-btn:hover:not(:disabled) {
		background: #545b62;
	}

	.refresh-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		background: #f8d7da;
		color: #721c24;
		border: 1px solid #f5c6cb;
		border-radius: 4px;
		padding: 0.75rem;
		margin-bottom: 1rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.close-error {
		background: none;
		border: none;
		color: #721c24;
		cursor: pointer;
		font-size: 1.2rem;
		padding: 0;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.loading, .empty {
		text-align: center;
		padding: 2rem;
		color: #666;
		font-style: italic;
	}

	.document-list {
		space-y: 0.5rem;
	}

	.document-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		border: 1px solid #eee;
		border-radius: 4px;
		margin-bottom: 0.5rem;
	}

	.document-item:hover {
		background: #f8f9fa;
	}

	.document-info {
		flex: 1;
	}

	.filename {
		font-weight: 500;
		color: #333;
		margin-bottom: 0.25rem;
	}

	.hash {
		font-size: 0.85rem;
		color: #666;
		font-family: monospace;
	}

	.delete-btn {
		padding: 0.5rem 1rem;
		background: #dc3545;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.delete-btn:hover:not(:disabled) {
		background: #c82333;
	}

	.delete-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.summary {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #eee;
		font-size: 0.9rem;
		color: #666;
		text-align: center;
	}
</style>