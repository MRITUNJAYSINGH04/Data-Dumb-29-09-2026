from backend.app.adapters.registry import tool_registry

# Layer 1: Infrastructure & Perimeter Recon (10)
from backend.app.adapters.layer1_infrastructure import (
    SpiderFootAdapter, TheHarvesterAdapter, Sublist3rAdapter, AmassAdapter,
    DNSRecordAdapter, FierceAdapter, WAFW00FAdapter, ShodanAdapter,
    CensysAdapter, SecurityTrailsAdapter
)

# Layer 2: Corporate & Business Intelligence (10)
from backend.app.adapters.layer2_corporate import (
    BuiltWithAdapter, CrunchbaseAdapter, ClearbitAdapter, HunterAdapter,
    SnovIoAdapter, ZoomInfoProxyAdapter, ApolloAdapter, OpenCorporatesAdapter,
    SecEdgarAdapter, JobBoardScraperAdapter
)

# Layer 3: Professional & Identity Recon (10)
from backend.app.adapters.layer3_identity import (
    SherlockAdapter, MaigretAdapter, SocialScanAdapter, GHuntAdapter,
    HoleheAdapter, BlackbirdAdapter, H8mailAdapter, MetagoofilAdapter,
    SkyMemAdapter, TwintArchiveAdapter
)

# Layer 4: Developer & Code Intelligence (10)
from backend.app.adapters.layer4_developer import (
    GitHubAdapter, GitLabAdapter, NpmjsAdapter, PypiAdapter,
    DockerHubAdapter, HackerNewsAdapter, StackOverflowAdapter,
    PastebinAdapter, BugcrowdHackerOneAdapter, PackagistAdapter
)

# Layer 5: Media, News, & Synthesis (10)
from backend.app.adapters.layer5_media_synthesis import (
    NewsApiAdapter, GoogleNewsRssAdapter, WaybackMachineAdapter,
    CommonCrawlAdapter, WikipediaAdapter, XTwitterPublicAdapter,
    RedditAdapter, LegalGazetteAdapter, PatentOfficeAdapter,
    GodsEyeAiSynthesisAdapter
)

# Clear and register all 50 tactical adapters
tool_registry._adapters.clear()

# Layer 1
tool_registry.register(SpiderFootAdapter())
tool_registry.register(TheHarvesterAdapter())
tool_registry.register(Sublist3rAdapter())
tool_registry.register(AmassAdapter())
tool_registry.register(DNSRecordAdapter())
tool_registry.register(FierceAdapter())
tool_registry.register(WAFW00FAdapter())
tool_registry.register(ShodanAdapter())
tool_registry.register(CensysAdapter())
tool_registry.register(SecurityTrailsAdapter())

# Layer 2
tool_registry.register(BuiltWithAdapter())
tool_registry.register(CrunchbaseAdapter())
tool_registry.register(ClearbitAdapter())
tool_registry.register(HunterAdapter())
tool_registry.register(SnovIoAdapter())
tool_registry.register(ZoomInfoProxyAdapter())
tool_registry.register(ApolloAdapter())
tool_registry.register(OpenCorporatesAdapter())
tool_registry.register(SecEdgarAdapter())
tool_registry.register(JobBoardScraperAdapter())

# Layer 3
tool_registry.register(SherlockAdapter())
tool_registry.register(MaigretAdapter())
tool_registry.register(SocialScanAdapter())
tool_registry.register(GHuntAdapter())
tool_registry.register(HoleheAdapter())
tool_registry.register(BlackbirdAdapter())
tool_registry.register(H8mailAdapter())
tool_registry.register(MetagoofilAdapter())
tool_registry.register(SkyMemAdapter())
tool_registry.register(TwintArchiveAdapter())

# Layer 4
tool_registry.register(GitHubAdapter())
tool_registry.register(GitLabAdapter())
tool_registry.register(NpmjsAdapter())
tool_registry.register(PypiAdapter())
tool_registry.register(DockerHubAdapter())
tool_registry.register(HackerNewsAdapter())
tool_registry.register(StackOverflowAdapter())
tool_registry.register(PastebinAdapter())
tool_registry.register(BugcrowdHackerOneAdapter())
tool_registry.register(PackagistAdapter())

# Layer 5
tool_registry.register(NewsApiAdapter())
tool_registry.register(GoogleNewsRssAdapter())
tool_registry.register(WaybackMachineAdapter())
tool_registry.register(CommonCrawlAdapter())
tool_registry.register(WikipediaAdapter())
tool_registry.register(XTwitterPublicAdapter())
tool_registry.register(RedditAdapter())
tool_registry.register(LegalGazetteAdapter())
tool_registry.register(PatentOfficeAdapter())
tool_registry.register(GodsEyeAiSynthesisAdapter())

__all__ = ["tool_registry"]
