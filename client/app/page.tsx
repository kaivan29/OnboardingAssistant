import { PageLayout } from "@/components/landing-page/PageLayout";
import { Header } from "@/components/landing-page/Header";
import { Hero } from "@/components/landing-page/Hero";
import { Partners } from "@/components/landing-page/Partners";

export default function Home() {
  return (
    <PageLayout>
      <Header />
      <Hero />
      <Partners />
    </PageLayout>
  );
}
