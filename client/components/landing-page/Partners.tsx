import { Github, Trello, Slack, Database, Server } from "lucide-react";

export function Partners() {
  const partners = [
    { name: "GitHub", icon: Github },
    { name: "Linear", icon: Trello }, // Using Trello icon as placeholder for Linear if not available, or just generic
    { name: "Slack", icon: Slack },
    { name: "Postgres", icon: Database },
    { name: "AWS", icon: Server },
  ];

  return (
    <div className="py-12 bg-white">
      <div className="text-center mb-8">
        <h3 className="text-lg font-medium text-gray-900">Our Trusted Partners</h3>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-8 px-8 lg:px-12 items-center justify-items-center opacity-75 grayscale hover:grayscale-0 transition-all duration-500">
        {partners.map((partner) => (
          <div key={partner.name} className="flex items-center gap-2 group cursor-default">
            <partner.icon className="h-6 w-6 text-black group-hover:scale-110 transition-transform" />
            <span className="text-lg font-semibold text-black">{partner.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
