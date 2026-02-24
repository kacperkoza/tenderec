import { Header } from "@/components/layout/header";
import { RecommendationList } from "@/components/recommendations/recommendation-list";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-6 py-8">
        <RecommendationList />
      </main>
    </div>
  );
}
