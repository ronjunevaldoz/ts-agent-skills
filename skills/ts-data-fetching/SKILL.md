---
name: ts-data-fetching
description: >
  TanStack Query (React Query) as the client-side server-state layer — query
  keys, `useQuery`/`useMutation`, cache invalidation, and optimistic updates.
  This is the explicit companion to `ts-state-management`, which says fetched
  API data does NOT belong in Redux/Zustand/Context and routes it here instead.
  Covers why a dedicated server-state library beats hand-rolled
  `useEffect`/`useState` fetching, and how tRPC's built-in React Query
  integration (`ts-api-layer`) wraps this same layer automatically.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - TanStack Query
    - React Query
    - useQuery
    - useMutation
    - query keys
    - cache invalidation
    - optimistic updates
    - server state
    - invalidateQueries
    - queryClient
    - refetch on window focus
    - request deduplication
    - onMutate
    - staleTime
---

## When to Use This Skill

Use when you need to:
- Fetch server data into a React component instead of hand-rolling `useEffect` +
  `useState` + a loading boolean
- Structure query keys so a mutation can invalidate exactly the cache it affected
- Update the UI instantly on a mutation, before the server responds, with a
  correct rollback on failure
- Decide whether fetched data belongs in TanStack Query or a client store

**Trigger keywords:** TanStack Query, React Query, useQuery, useMutation, query key,
queryClient, invalidateQueries, optimistic update, onMutate, staleTime, cacheTime,
refetch, QueryClientProvider, prefetchQuery.

**Freshness rule:** TanStack Query v4 → v5 renamed several options (`cacheTime` →
`gcTime`, object-only function signatures) — recheck the installed
`@tanstack/react-query` major version's docs before writing new query code.

---

## Recommendation First

**TanStack Query for every piece of state whose source of truth is a server.** Never
`useEffect` + `useState` for a fetch, and never put fetched data in Redux/Zustand/
Context — see `ts-state-management`'s "Server-State Trap" section, which sends that
decision here.

Why a dedicated library instead of `useEffect`:
- **Caching** — a second component asking for the same `["posts", 1]` key gets the
  cached value instantly, no duplicate request
- **Request deduplication** — two components mounting simultaneously and calling the
  same query key fire one network request, not two
- **Refetch-on-window-focus** — data goes stale silently in a background tab;
  switching back triggers a refetch automatically, no manual polling
- **Built-in loading/error/success state** — no `useState<boolean>` for `loading`,
  no `useState<Error | null>` for `error`, no race condition where a stale response
  overwrites a newer one
- **Background refetching** — a `staleTime`-expired query refetches without
  unmounting the UI first, so the screen never flashes back to a spinner for data it
  already has

```tsx
// ❌ Wrong — hand-rolled, no caching, no dedup, a race condition waiting to happen
function PostView({ id }: { id: string }) {
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/posts/${id}`)
      .then((r) => r.json())
      .then(setPost)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [id]); // no cancellation — a fast id change can let a stale response win

  if (loading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  return <h1>{post?.title}</h1>;
}

// ✓ Correct — caching, dedup, loading/error state, refetch-on-focus, all free
function PostView({ id }: { id: string }) {
  const { data: post, isLoading, error } = useQuery({
    queryKey: ["posts", id],
    queryFn: () => fetch(`/api/posts/${id}`).then((r) => r.json() as Promise<Post>),
  });

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  return <h1>{post?.title}</h1>;
}
```

---

## Query Keys — Structure Them for Precise Invalidation

A query key is an array, not a string — array structure is what lets a mutation
invalidate exactly the slice of cache it affected, no more:

```ts
["posts"]                 // all posts — a list view
["posts", { page: 2 }]     // a specific paginated list
["posts", postId]          // one post
["posts", postId, "comments"] // that post's comments — nested resource
```

```ts
// Invalidate everything under "posts" — every list AND every individual post refetches
queryClient.invalidateQueries({ queryKey: ["posts"] });

// Invalidate just this one post — lists and other posts are untouched
queryClient.invalidateQueries({ queryKey: ["posts", postId] });
```

TanStack Query matches by prefix: invalidating `["posts"]` matches
`["posts", 1]`, `["posts", { page: 2 }]`, and `["posts", 1, "comments"]` alike,
because they all start with `"posts"`. This is the entire reason to keep keys
hierarchical (`["posts", postId]`, not `["post-" + postId]` as a single string) —
a flat string key can't be partially matched.

```ts
// query-keys.ts — centralize keys so a typo can't silently miss an invalidation
export const postKeys = {
  all: ["posts"] as const,
  list: (filters: PostFilters) => [...postKeys.all, "list", filters] as const,
  detail: (id: string) => [...postKeys.all, "detail", id] as const,
};

// usage
useQuery({ queryKey: postKeys.detail(id), queryFn: () => fetchPost(id) });
queryClient.invalidateQueries({ queryKey: postKeys.all }); // everything post-related
```

---

## Mutations — `useMutation` + `invalidateQueries`

A mutation doesn't touch the cache on its own — call `invalidateQueries` in
`onSuccess` to tell TanStack Query the server-side data it cached is now stale:

```tsx
function CreatePostForm() {
  const queryClient = useQueryClient();

  const createPost = useMutation({
    mutationFn: (input: { title: string; body: string }) =>
      fetch("/api/posts", {
        method: "POST",
        body: JSON.stringify(input),
      }).then((r) => r.json() as Promise<Post>),
    onSuccess: () => {
      // refetches every "posts" list — the new post shows up without a page reload
      queryClient.invalidateQueries({ queryKey: postKeys.all });
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const form = new FormData(e.currentTarget);
        createPost.mutate({
          title: form.get("title") as string,
          body: form.get("body") as string,
        });
      }}
    >
      <input name="title" />
      <textarea name="body" />
      <button type="submit" disabled={createPost.isPending}>
        {createPost.isPending ? "Saving..." : "Save"}
      </button>
    </form>
  );
}
```

`invalidateQueries` marks matching queries stale and refetches any that are
currently rendered — it doesn't synchronously update the cache with the mutation's
response. For an instant UI update before the refetch lands, use an optimistic
update instead.

---

## Optimistic Updates — `onMutate` / `onError` / `onSettled`

Update the cache immediately, before the server responds, and roll back if the
mutation fails. Three lifecycle hooks do this correctly:

```tsx
function useToggleLike(postId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (liked: boolean) =>
      fetch(`/api/posts/${postId}/like`, {
        method: "POST",
        body: JSON.stringify({ liked }),
      }),

    // Runs before the request fires — apply the optimistic change here
    onMutate: async (liked) => {
      // stop any in-flight refetch from clobbering the optimistic value
      await queryClient.cancelQueries({ queryKey: postKeys.detail(postId) });

      // snapshot the current cache so onError can restore it exactly
      const previousPost = queryClient.getQueryData<Post>(postKeys.detail(postId));

      // write the optimistic value into the cache immediately
      queryClient.setQueryData<Post>(postKeys.detail(postId), (old) =>
        old ? { ...old, liked, likeCount: old.likeCount + (liked ? 1 : -1) } : old,
      );

      // returned value becomes `context` in onError/onSettled
      return { previousPost };
    },

    // Runs on failure — roll back to the exact snapshot from onMutate
    onError: (_err, _liked, context) => {
      if (context?.previousPost) {
        queryClient.setQueryData(postKeys.detail(postId), context.previousPost);
      }
    },

    // Runs after success OR error — resync with the server regardless of outcome
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: postKeys.detail(postId) });
    },
  });
}
```

Why all three hooks, not just `onMutate`: `onMutate`'s optimistic write can be
wrong (a race with another update, a server-side side effect the client can't
predict) — `onSettled`'s invalidation is what guarantees the cache eventually
matches the server regardless of whether the optimistic guess was right.
`cancelQueries` in `onMutate` matters because an in-flight background refetch
that resolves *after* the optimistic write would otherwise overwrite it with
stale pre-mutation data.

---

## Pairing With tRPC (`ts-api-layer`)

tRPC's React Query integration wraps this exact layer — `trpc.post.byId.useQuery`
and `trpc.post.create.useMutation` are TanStack Query's `useQuery`/`useMutation`
underneath, with the query key generated from the procedure path and input:

```tsx
const utils = trpc.useUtils();

const createPost = trpc.post.create.useMutation({
  onSuccess: () => utils.post.byId.invalidate(), // same invalidateQueries under the hood
});
```

Everything in this skill — key structure, `onMutate`/`onError`/`onSettled`,
`staleTime` — applies identically inside a tRPC procedure's generated hooks. Use
plain `useQuery`/`useMutation` (this skill) for REST endpoints; use tRPC's wrapped
hooks for tRPC procedures. Don't hand-write a `queryKey` for a tRPC call — the
integration derives it from the procedure path automatically, and a hand-written
key won't match what `utils.post.byId.invalidate()` targets.

---

## Server State vs Client State

This is the same boundary `ts-state-management` draws, from the other side: if the
data's source of truth lives on a server, it belongs in TanStack Query, full stop —
never in Redux, Zustand, or Context, even "just temporarily" or "just to avoid a
prop-drill." Read `ts-state-management`'s "The Server-State Trap" section before
building any store that holds fetched data.

The test: does this state have a server-side owner that can change it out from
under the client (another user, another tab, a background job)? If yes, it's
TanStack Query's job. If the UI itself invented the state and no server copy
exists (is this modal open, which step of the wizard), it's a client store's job.

---

## Common Anti-Patterns

- **Fetched data in `useState`/Redux/Zustand, with hand-rolled loading/error/
  refetch logic.** This is the exact mistake `ts-state-management` calls out —
  every one of loading state, error state, cache invalidation, and
  refetch-on-focus has to be rebuilt by hand, and usually one of them is missing
  or wrong.
- **Invalidating too broadly.** `queryClient.invalidateQueries({ queryKey:
  ["posts"] })` after editing one comment refetches every post list on screen.
  Structure keys so the invalidation call can target `["posts", postId]` or
  `["posts", postId, "comments"]` instead of the whole `["posts"]` tree.
- **No error boundary around a query that can fail.** A failed `useQuery` sets
  `error`, it doesn't throw by default — a component that only checks
  `data`/`isLoading` and ignores `error` renders as if the fetch silently
  succeeded with `undefined`. Either check `error` explicitly or pass `throwOnError:
  true` and wrap the tree in an error boundary.
- **Skipping `onMutate`'s cancel + snapshot in an optimistic update.** Writing the
  optimistic value without `cancelQueries` first lets an in-flight background
  refetch land afterward and silently overwrite it; skipping the snapshot means
  `onError` has nothing correct to roll back to.
- **Using `useEffect` to sync `useQuery`'s `data` into local `useState`.** This
  creates a second copy of the same data that can go out of sync with the cache —
  read `data` directly from `useQuery` at render time instead.

---

## Related Skills

- `ts-state-management` — the client-state counterpart; read its "Server-State
  Trap" section for the boundary this skill's data lives on the other side of
- `ts-api-layer` — tRPC's `useQuery`/`useMutation` wrap this same TanStack Query
  layer automatically; use plain TanStack Query directly for REST endpoints
- `ts-validation-schema` — Zod schemas for validating a `queryFn`'s response shape
- `ts-forms` — form submission usually calls a `useMutation`, not a raw `fetch`
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
