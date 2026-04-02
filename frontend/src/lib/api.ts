/** API client for Yado backend. */

const BASE = '/api';

export interface DateOption {
	id: string;
	date: string;
	start_time: string | null;
	end_time: string | null;
}

export interface Vote {
	id: string;
	participant_id: string;
	date_option_id: string;
	choice: 'yes' | 'no' | 'maybe';
}

export interface Participant {
	id: string;
	name: string;
	votes: Vote[];
}

export interface Poll {
	id: string;
	title: string;
	description: string;
	timezone: string;
	created_at: string;
	closed: boolean;
	date_options: DateOption[];
	participants: Participant[];
}

export interface PollCreated {
	id: string;
	admin_token: string;
	poll: Poll;
}

export interface VoteResponse {
	participant_id: string;
	edit_token: string;
}

export interface DateOptionInput {
	date: string;
	start_time?: string | null;
	end_time?: string | null;
}

export interface VoteInput {
	date_option_id: string;
	choice: 'yes' | 'no' | 'maybe';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		headers: { 'Content-Type': 'application/json' },
		...init
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(`API error ${res.status}: ${body}`);
	}
	return res.json();
}

export function createPoll(data: {
	title: string;
	description?: string;
	timezone?: string;
	date_options: DateOptionInput[];
}): Promise<PollCreated> {
	return request('/polls', { method: 'POST', body: JSON.stringify(data) });
}

export function getPoll(id: string): Promise<Poll> {
	return request(`/polls/${id}`);
}

export function vote(
	pollId: string,
	data: { name: string; edit_token?: string | null; votes: VoteInput[] }
): Promise<VoteResponse> {
	return request(`/polls/${pollId}/vote`, { method: 'POST', body: JSON.stringify(data) });
}

export function closePoll(pollId: string, adminToken: string): Promise<Poll> {
	return request(`/polls/${pollId}/close?admin_token=${encodeURIComponent(adminToken)}`, {
		method: 'POST'
	});
}

export function deletePoll(pollId: string, adminToken: string): Promise<void> {
	return request(`/polls/${pollId}?admin_token=${encodeURIComponent(adminToken)}`, {
		method: 'DELETE'
	});
}

/** Connect to real-time updates for a poll with auto-reconnect. */
export function subscribePoll(
	pollId: string,
	onUpdate: (poll: Poll) => void
): { close: () => void } {
	let closed = false;
	let ws: WebSocket | null = null;
	let retryMs = 1000;

	function connect() {
		if (closed) return;
		const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		ws = new WebSocket(`${proto}//${window.location.host}/api/polls/${pollId}/ws`);
		ws.onopen = () => {
			retryMs = 1000;
		};
		ws.onmessage = (e) => {
			const msg = JSON.parse(e.data);
			if (msg.type === 'poll_updated') {
				onUpdate(msg.poll);
			}
		};
		ws.onclose = () => {
			if (!closed) setTimeout(connect, retryMs);
			retryMs = Math.min(retryMs * 2, 30000);
		};
	}

	connect();
	return {
		close: () => {
			closed = true;
			ws?.close();
		}
	};
}
