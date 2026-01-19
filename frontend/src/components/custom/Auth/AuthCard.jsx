import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function AuthCard({ heading, subheading, children }) {
    return (
        <Card className="border-slate-200/70 bg-white shadow-sm">
        <CardHeader className="space-y-2">
            {/* Real semantic heading for accessibility + tests */}
            <h2 className="text-xl font-semibold text-slate-900">{heading}</h2>

            {subheading ? (
            <p className="text-sm text-slate-600">{subheading}</p>
            ) : null}
        </CardHeader>

        <CardContent className="space-y-4">{children}</CardContent>
        </Card>
    );
}
