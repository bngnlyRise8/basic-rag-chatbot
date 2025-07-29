<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{
		uploaded: { filename: string; chunks: number };
	}>();

	let dragover = false;
	let uploading = false;
	let uploadStatus = '';
	let fileInput: HTMLInputElement;

	const API_BASE = 'http://localhost:8000/api';

	async function uploadFile(file: File) {
		if (!file.type.includes('pdf')) {
			uploadStatus = 'Only PDF files are supported';
			return;
		}

		uploading = true;
		uploadStatus = 'Uploading...';

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

			const data = await response.json();
			uploadStatus = `Successfully uploaded: ${data.filename} (${data.chunks} chunks)`;
			
			dispatch('uploaded', {
				filename: data.filename,
				chunks: data.chunks
			});

		} catch (error) {
			console.error('Upload error:', error);
			uploadStatus = `Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`;
		} finally {
			uploading = false;
		}
	}

	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) {
			uploadFile(file);
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		dragover = false;
		
		const file = event.dataTransfer?.files[0];
		if (file) {
			uploadFile(file);
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		dragover = true;
	}

	function handleDragLeave() {
		dragover = false;
	}

	function triggerFileInput() {
		fileInput.click();
	}
</script>

<div class="upload-container">
	<div 
		class="upload-area"
		class:dragover
		class:uploading
		on:drop={handleDrop}
		on:dragover={handleDragOver}
		on:dragleave={handleDragLeave}
		on:click={triggerFileInput}
		role="button"
		tabindex="0"
		on:keydown={(e) => e.key === 'Enter' && triggerFileInput()}
	>
		{#if uploading}
			<div class="upload-spinner"></div>
			<p>Uploading...</p>
		{:else}
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
				<polyline points="17,8 12,3 7,8"/>
				<line x1="12" y1="3" x2="12" y2="15"/>
			</svg>
			<p>
				Drop PDF files here or <span class="link">click to browse</span>
			</p>
		{/if}
	</div>

	<input
		bind:this={fileInput}
		type="file"
		accept=".pdf"
		on:change={handleFileSelect}
		style="display: none"
	/>

	{#if uploadStatus}
		<div class="status" class:error={uploadStatus.includes('failed')}>
			{uploadStatus}
		</div>
	{/if}
</div>

<style>
	.upload-container {
		margin-bottom: 2rem;
	}

	.upload-area {
		border: 2px dashed #ddd;
		border-radius: 8px;
		padding: 2rem;
		text-align: center;
		cursor: pointer;
		transition: all 0.3s ease;
		background: #fafafa;
	}

	.upload-area:hover,
	.upload-area.dragover {
		border-color: #007bff;
		background: #f0f8ff;
	}

	.upload-area.uploading {
		pointer-events: none;
		opacity: 0.7;
	}

	.upload-area svg {
		color: #666;
		margin-bottom: 1rem;
	}

	.upload-area p {
		margin: 0;
		color: #666;
		font-size: 1rem;
	}

	.link {
		color: #007bff;
		text-decoration: underline;
	}

	.upload-spinner {
		width: 32px;
		height: 32px;
		border: 3px solid #f3f3f3;
		border-top: 3px solid #007bff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.status {
		margin-top: 1rem;
		padding: 0.75rem;
		border-radius: 4px;
		background: #d4edda;
		color: #155724;
		border: 1px solid #c3e6cb;
	}

	.status.error {
		background: #f8d7da;
		color: #721c24;
		border-color: #f5c6cb;
	}
</style>