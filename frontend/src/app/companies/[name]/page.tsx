"use client";

import { use, useState } from "react";
import { useCompany, useCreateCompany } from "@/hooks/use-company";
import { NotFoundError } from "@/lib/api-client";
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

function ProfileSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <div>{children}</div>
    </div>
  );
}

function TagList({ items }: { items: string[] }) {
  if (items.length === 0) {
    return <span className="text-sm text-muted-foreground">Brak</span>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className="inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-medium"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function CreateProfileForm({
  companyName,
  onSuccess,
}: {
  companyName: string;
  onSuccess: () => void;
}) {
  const [description, setDescription] = useState("");
  const { mutate, isPending, error } = useCreateCompany();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = description.trim();
    if (!trimmed) return;

    mutate(
      { name: companyName, data: { description: trimmed } },
      { onSuccess }
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Utwórz profil firmy</CardTitle>
        <CardDescription>
          Opisz swoją firmę, a my wygenerujemy profil dopasowania do przetargów
          dla <span className="font-medium text-foreground">{companyName}</span>.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="company-description">Opis firmy</Label>
            <Textarea
              id="company-description"
              placeholder="Opisz czym zajmuje się Twoja firma, w jakich branżach działa, jakie usługi świadczy oraz inne istotne informacje..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isPending}
              required
              rows={6}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error.message}</p>
          )}

          <Button type="submit" disabled={isPending} className="w-full">
            {isPending ? "Tworzenie profilu..." : "Utwórz profil"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function ProfileView({
  company,
}: {
  company: NonNullable<ReturnType<typeof useCompany>["data"]>;
}) {
  const { profile, created_at } = company;
  const { company_info, matching_criteria } = profile;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">{company_info.name}</CardTitle>
        <CardDescription>
          Profil utworzony{" "}
          {new Date(created_at).toLocaleDateString("pl-PL", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <ProfileSection title="Branże">
          <TagList items={company_info.industries} />
        </ProfileSection>

        <ProfileSection title="Kategorie usług">
          <TagList items={matching_criteria.service_categories} />
        </ProfileSection>

        <ProfileSection title="Kody CPV">
          <TagList items={matching_criteria.cpv_codes} />
        </ProfileSection>

        <ProfileSection title="Instytucje zamawiające">
          <TagList items={matching_criteria.target_authorities} />
        </ProfileSection>

        <ProfileSection title="Geografia">
          <p className="text-sm">
            {matching_criteria.geography.primary_country || "Nie określono"}
          </p>
        </ProfileSection>
      </CardContent>
    </Card>
  );
}

export default function CompanyProfilePage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = use(params);
  const decodedName = decodeURIComponent(name);
  const { data: company, isLoading, error, refetch } = useCompany(decodedName);

  const isNotFound = error instanceof NotFoundError;

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl">
        <Card>
          <CardContent className="py-12">
            <div className="space-y-4">
              <div className="h-6 w-1/3 animate-pulse rounded bg-muted" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
              <div className="h-4 w-3/4 animate-pulse rounded bg-muted" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isNotFound) {
    return (
      <div className="mx-auto max-w-2xl">
        <CreateProfileForm companyName={decodedName} onSuccess={() => refetch()} />
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

  if (!company) return null;

  return (
    <div className="mx-auto max-w-2xl">
      <ProfileView company={company} />
    </div>
  );
}
