---
name: ts-forms
description: >
  React Hook Form + Zod resolver integration — uncontrolled inputs by default,
  field-level errors, submit gating while pending, and one Zod schema reused
  for both client validation and Server Action re-validation. The client
  check is UX; the server check on the same schema is the actual security
  boundary.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - React Hook Form
    - zodResolver
    - form validation
    - field errors
    - submit gating
    - useForm
    - controlled vs uncontrolled
    - async validation
    - Server Action
    - FormData
    - isSubmitting
    - schema reuse
---

## When to Use This Skill

Use when you need to:
- Build any form with more than one or two fields
- Show field-level validation errors on blur/change/submit
- Disable submit while a mutation is in flight, so a double-click can't fire twice
- Re-validate a form's `FormData` inside a Server Action, using the same schema
  the client already validated with
- Add an async check (email already taken, username available) without hand-rolling
  debounce/race-condition logic

**Trigger keywords:** React Hook Form, useForm, zodResolver, form validation, field
errors, formState.errors, isSubmitting, register, Controller, FormData validation,
async validation, uncontrolled input.

**Freshness rule:** React Hook Form's resolver package (`@hookform/resolvers`) and
Zod both ship breaking changes across majors — recheck `zodResolver`'s current import
path and Zod's `.safeParse` return shape before wiring a new form.

---

## Recommendation First

**React Hook Form + `zodResolver`**, one Zod schema shared between client and server,
default. Not hand-rolled `useState` per field.

Why:
- RHF's `register` wires inputs as **uncontrolled** — the DOM owns the value, RHF reads
  it via ref, not via a `value`/`onChange` round-trip through React state. A 10-field
  form with `useState` per field re-renders the whole form on every keystroke in every
  field; RHF re-renders only on submit, blur, or the field(s) that fail validation.
- `zodResolver(schema)` bridges Zod straight into RHF's `formState.errors` — the same
  schema that produces the TS type (`z.infer<typeof schema>`) is the validation logic.
  No parallel hand-written `validateEmail()` that can drift from what the type says
  is valid. This is `ts-validation-schema`'s "one schema, reused everywhere" principle
  applied to forms specifically.
- Validation timing (`mode: "onBlur"` vs `"onChange"` vs `"onSubmit"`) is one config
  option, not a `useEffect` per field watching for changes.

Reach for `Controller` only when wrapping a component that doesn't expose a raw DOM
`ref` (a shadcn/ui `<Select>`, a date picker, anything Radix-based) — plain `<input>`/
`<textarea>`/`<select>` always use `register`.

---

## A Complete Form: Email + Password

```tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const SignInSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
type SignInInput = z.infer<typeof SignInSchema>;

export function SignInForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignInInput>({
    resolver: zodResolver(SignInSchema),
    mode: "onBlur", // validate on blur, re-validate that field on every change after
  });

  async function onSubmit(data: SignInInput) {
    const res = await fetch("/api/sign-in", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Sign-in failed");
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <label htmlFor="email">Email</label>
      <input id="email" type="email" {...register("email")} />
      {errors.email && <p role="alert">{errors.email.message}</p>}

      <label htmlFor="password">Password</label>
      <input id="password" type="password" {...register("password")} />
      {errors.password && <p role="alert">{errors.password.message}</p>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
```

`isSubmitting` is derived by RHF from the `onSubmit` handler's returned promise — no
manual `useState<boolean>` for a pending flag. `noValidate` on the `<form>` suppresses
the browser's native bubble validation so Zod's messages are the only ones shown.

---

## Server-Side Re-Validation — The Same Schema, Again

Client validation is UX (instant feedback, no round trip). It is not a security
boundary — anyone can call the endpoint directly with `curl`, bypassing the browser
entirely. The Server Action must re-run the identical schema against the raw
`FormData`.

```ts
// schemas/sign-in.ts — imported by both the client form above and the action below
import { z } from "zod";

export const SignInSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
```

```ts
// app/actions.ts
"use server";
import { SignInSchema } from "@/schemas/sign-in";

export async function signIn(_prevState: unknown, formData: FormData) {
  const parsed = SignInSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { errors: parsed.error.flatten().fieldErrors };
  }
  // parsed.data is the same SignInInput type the client form used
  const user = await verifyCredentials(parsed.data);
  if (!user) return { errors: { email: ["Invalid email or password"] } };
  // ... set session, redirect
}
```

Import `SignInSchema` from one shared module (see `ts-validation-schema`) — never
redefine the rules in the action. If the schema only lived in the client component,
a request that skips the browser skips every check.

---

## Async Validation — "Email Already Taken"

RHF supports an async validator per field via `validate` in `register`'s rule object,
or a debounced check wired through `trigger()`. The simplest correct pattern is a
Zod `.refine` with `async`, run only on blur (not on every keystroke) so it doesn't
hammer the API:

```ts
const SignUpSchema = z.object({
  email: z
    .string()
    .email()
    .refine(
      async (email) => {
        const res = await fetch(`/api/check-email?email=${encodeURIComponent(email)}`);
        const { taken } = await res.json();
        return !taken;
      },
      { message: "Email is already registered" },
    ),
  password: z.string().min(8),
});
```

```tsx
useForm({
  resolver: zodResolver(SignUpSchema),
  mode: "onBlur", // async check fires on blur, not on every keystroke
});
```

`zodResolver` awaits async `.refine` automatically — no separate `onBlur` handler or
manual debounce needed. Do add a debounce at the fetch layer (or an `AbortController`
that cancels the previous request) if the field can realistically be re-blurred faster
than the API responds; that's the one case where the given rung of the ladder — the
resolver's built-in awaiting — isn't quite enough on its own.

---

## Common Anti-Patterns

- **Trusting client-side validation alone** — skipping the Server Action re-validation
  because "the form already checked it." The client is fully attacker-controlled;
  `SignInSchema.safeParse` must run again server-side on the raw `FormData`. This is
  the actual security hole, not a style nit.
- **A separate hand-written validation function** (`function isValidEmail(s: string)`)
  living next to the Zod schema instead of being expressed in it. The two drift the
  first time either one changes — one schema is the single source of truth, per
  `ts-validation-schema`.
- **Not disabling the submit button during submission** — a slow network plus an
  impatient double-click fires the mutation twice. Wire `disabled={isSubmitting}`
  (or `isPending` from `useActionState`/`useFormStatus`) every time, not just on
  forms where it "seems slow."
- **Controlled inputs (`value`/`onChange` + `useState`) for plain text fields** when
  `register` already gives uncontrolled behavior for free — re-introduces a re-render
  per keystroke that RHF was chosen specifically to avoid. Reach for `Controller`
  only for non-native inputs that need it.
- **Re-deriving the TS type by hand** (`interface SignInInput { email: string; ... }`)
  instead of `z.infer<typeof SignInSchema>` — the interface silently goes stale the
  next time a field is added to the schema.

---

## Related Skills

- `ts-validation-schema` — the "one schema, reused everywhere" principle this skill
  applies specifically to forms; owns Zod schema design and shared-schema placement
- `ts-nextjs-app-router` — Server Actions and `FormData` handling this skill's
  server-side re-validation builds on
- `ts-expert` — routing and build order for the full skill set
- `ts-state-management` — where submitted-but-not-yet-persisted UI state lives when a
  form is part of a larger flow

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
