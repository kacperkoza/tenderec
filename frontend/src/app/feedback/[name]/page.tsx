"use client";

import { use, useState } from "react";
import { useFeedbacks, useCreateFeedback } from "@/hooks/use-feedback";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Feedback } from "@/types/api";

function FeedbackForm({
  companyName,
  isPending,
  error,
  onSubmit,
}: {
  companyName: string;
  isPending: boolean;
  error: Error | null;
  onSubmit: (comment: string) => void;
}) {
  const [comment, setComment] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = comment.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setComment("");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dodaj opinię</CardTitle>
        <CardDescription>
          Dodaj opinię dotyczącą przetargów dla firmy{" "}
          <span className="font-medium text-foreground">{companyName}</span>.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="feedback-comment">Komentarz</Label>
            <Textarea
              id="feedback-comment"
              placeholder="Wpisz swoją opinię dotyczącą przetargu..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              disabled={isPending}
              required
              rows={4}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error.message}</p>
          )}

          <Button type="submit" disabled={isPending} className="w-full">
            {isPending ? "Dodawanie..." : "Dodaj opinię"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function FeedbackList({ feedbacks }: { feedbacks: Feedback[] }) {
  if (feedbacks.length === 0) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-sm text-muted-foreground">
            Brak opinii. Dodaj pierwszą opinię powyżej.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {feedbacks.map((feedback) => (
        <Card key={feedback.id}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              {feedback.id}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{feedback.feedback_comment}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function FeedbackPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = use(params);
  const decodedName = decodeURIComponent(name);
  const { data, isLoading, error, refetch } = useFeedbacks(decodedName);
  const {
    mutate,
    isPending,
    error: createError,
  } = useCreateFeedback();

  function handleAddFeedback(comment: string) {
    mutate({ company: decodedName, data: { feedback_comment: comment } });
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl">
        <Card>
          <CardContent className="py-12">
            <div className="space-y-4">
              <div className="h-6 w-1/3 animate-pulse rounded bg-muted" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Błąd</CardTitle>
            <CardDescription>{error.message}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => refetch()}>
              Spróbuj ponownie
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Opinie o przetargach</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Opinie dotyczące firmy{" "}
          <span className="font-medium text-foreground">{decodedName}</span>
        </p>
      </div>

      <FeedbackForm
        companyName={decodedName}
        isPending={isPending}
        error={createError}
        onSubmit={handleAddFeedback}
      />

      <div>
        <h2 className="mb-3 text-lg font-semibold">
          Dodane opinie ({data?.feedbacks.length ?? 0})
        </h2>
        <FeedbackList feedbacks={data?.feedbacks ?? []} />
      </div>
    </div>
  );
}
