<script lang="ts">
	import Chat from '$lib/components/Chat.svelte';
	import FileUpload from '$lib/components/FileUpload.svelte';
	import DocumentManager from '$lib/components/DocumentManager.svelte';

	let showUpload = true;

	function handleUpload(event: CustomEvent<{ filename: string; chunks: number }>) {
		console.log('File uploaded:', event.detail);
		// Refresh document list after upload
		documentManagerRef?.loadDocuments();
	}

	let documentManagerRef: DocumentManager;
</script>

<svelte:head>
	<title>AI Chatbot</title>
</svelte:head>

<main class="container">
	{#if showUpload}
		<div class="upload-section">
			<h1>AI Document Chatbot</h1>
			<p>Upload PDF documents and ask questions about their content.</p>
			
			<FileUpload on:uploaded={handleUpload} />
			
			<DocumentManager bind:this={documentManagerRef} />
			
			<button on:click={() => showUpload = false} class="continue-btn">
				Continue to Chat
			</button>
		</div>
	{:else}
		<div class="chat-section">
			<button on:click={() => showUpload = true} class="upload-btn">
				Upload More Documents
			</button>
			<Chat />
		</div>
	{/if}
</main>

<style>
	.container {
		padding: 1rem;
		max-width: 1200px;
		margin: 0 auto;
	}

	.upload-section {
		text-align: center;
		padding: 2rem;
		max-width: 600px;
		margin: 0 auto;
	}

	.upload-section h1 {
		color: #333;
		margin-bottom: 0.5rem;
	}

	.upload-section p {
		color: #666;
		margin-bottom: 2rem;
	}

	.continue-btn {
		padding: 0.75rem 2rem;
		background: #28a745;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
		margin-top: 1rem;
	}

	.continue-btn:hover {
		background: #218838;
	}

	.chat-section {
		height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.upload-btn {
		padding: 0.5rem 1rem;
		background: #6c757d;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		align-self: flex-start;
		margin-bottom: 1rem;
	}

	.upload-btn:hover {
		background: #545b62;
	}
</style>
