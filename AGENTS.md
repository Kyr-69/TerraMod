# Universal tModLoader 1.4+ AI Modding Specification

> Authoritative, decompilation-grounded reference for LLM agents generating Terraria 1.4.4+ mods.

## 1. CRITICAL 1.4 BREAKING CHANGES (ANTI-HALLUCINATION RULES)

Models trained on pre-1.4 code frequently hallucinate obsolete 1.3 methods. You MUST follow these modern 1.4 standards:

### Damage Classes
- NEVER write `Item.melee = true;`, `Item.ranged = true;`, `Item.magic = true;`, or `Item.summon = true;`
- ALWAYS use `Item.DamageType = DamageClass.Melee;`, `DamageClass.Ranged;`, `DamageClass.Magic;`, or `DamageClass.Summon;`

### Recipe System
- NEVER write `ModRecipe recipe = new ModRecipe(mod);` or `recipe.AddRecipe();`
- ALWAYS use the fluent 1.4 builder pattern on `CreateRecipe()`:
```csharp
Recipe recipe = CreateRecipe();
recipe.AddIngredient(ItemID.DirtBlock, 10);
recipe.AddTile(TileID.WorkBenches);
recipe.Register();
```

### Combat & Hit Hooks (`NPC.HitInfo`)
- In 1.3: `OnHitNPC(Player player, NPC target, int damage, float knockback, bool crit)`
- In 1.4: `OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone)`
- The `NPC.HitInfo` struct encapsulates `Damage`, `Knockback`, `Crit`, and `HitDirection`.

### Key Member & Field Renames in 1.4
| 1.3 Obsolete Member | 1.4 Ground-Truth Replacement | Description |
| :--- | :--- | :--- |
| `Terraria.ModLoader.ModType.mod` | `Terraria.ModLoader.ModType.Mod` | Field mod renamed to Mod in 1.4 |
| `Terraria.ModLoader.ModItem.item` | `Terraria.ModLoader.ModItem.Item` | Field item renamed to Item in 1.4 |
| `Terraria.ModLoader.EquipTexture.item` | `Terraria.ModLoader.EquipTexture.Item` | Field item renamed to Item in 1.4 |
| `Terraria.ModLoader.ModNPC.npc` | `Terraria.ModLoader.ModNPC.NPC` | Field npc renamed to NPC in 1.4 |
| `Terraria.ModLoader.ModPlayer.player` | `Terraria.ModLoader.ModPlayer.Player` | Field player renamed to Player in 1.4 |
| `Terraria.ModLoader.ModProjectile.projectile` | `Terraria.ModLoader.ModProjectile.Projectile` | Field projectile renamed to Projectile in 1.4 |
| `Terraria.ModLoader.ModMount.mountData` | `Terraria.ModLoader.ModMount.MountData` | Field mountData renamed to MountData in 1.4 |
| `Terraria.Item.modItem` | `Terraria.Item.ModItem` | Field modItem renamed to ModItem in 1.4 |
| `Terraria.NPC.modNPC` | `Terraria.NPC.ModNPC` | Field modNPC renamed to ModNPC in 1.4 |
| `Terraria.Projectile.modProjectile` | `Terraria.Projectile.ModProjectile` | Field modProjectile renamed to ModProjectile in 1.4 |
| `Terraria.Mount.MountData.modMountData` | `Terraria.Mount.MountData.ModMount` | Field modMountData renamed to ModMount in 1.4 |
| `Terraria.Gore.modGore` | `Terraria.Gore.ModGore` | Field modGore renamed to ModGore in 1.4 |
| `Terraria.ModLoader.TooltipLine.text` | `Terraria.ModLoader.TooltipLine.Text` | Field text renamed to Text in 1.4 |
| `Terraria.ModLoader.TooltipLine.mod` | `Terraria.ModLoader.TooltipLine.Mod` | Field mod renamed to Mod in 1.4 |
| `Terraria.ModLoader.TooltipLine.isModifier` | `Terraria.ModLoader.TooltipLine.IsModifier` | Field isModifier renamed to IsModifier in 1.4 |
| `Terraria.ModLoader.TooltipLine.isModifierBad` | `Terraria.ModLoader.TooltipLine.IsModifierBad` | Field isModifierBad renamed to IsModifierBad in 1.4 |
| `Terraria.ModLoader.TooltipLine.overrideColor` | `Terraria.ModLoader.TooltipLine.OverrideColor` | Field overrideColor renamed to OverrideColor in 1.4 |
| `Terraria.ModLoader.ModProjectile.aiType` | `Terraria.ModLoader.ModProjectile.AIType` | Field aiType renamed to AIType in 1.4 |
| `Terraria.ModLoader.ModProjectile.cooldownSlot` | `Terraria.ModLoader.ModProjectile.CooldownSlot` | Field cooldownSlot renamed to CooldownSlot in 1.4 |
| `Terraria.ModLoader.ModProjectile.drawOffsetX` | `Terraria.ModLoader.ModProjectile.DrawOffsetX` | Field drawOffsetX renamed to DrawOffsetX in 1.4 |
| `Terraria.ModLoader.ModProjectile.drawOriginOffsetY` | `Terraria.ModLoader.ModProjectile.DrawOriginOffsetY` | Field drawOriginOffsetY renamed to DrawOriginOffsetY in 1.4 |
| `Terraria.ModLoader.ModProjectile.drawOriginOffsetX` | `Terraria.ModLoader.ModProjectile.DrawOriginOffsetX` | Field drawOriginOffsetX renamed to DrawOriginOffsetX in 1.4 |
| `Terraria.ModLoader.ModProjectile.drawHeldProjInFrontOfHeldItemAndArms` | `Terraria.ModLoader.ModProjectile.DrawHeldProjInFrontOfHeldItemAndArms` | Field drawHeldProjInFrontOfHeldItemAndArms renamed to DrawHeldProjInFrontOfHeldItemAndArms in 1.4 |
| `Terraria.ModLoader.ModNPC.aiType` | `Terraria.ModLoader.ModNPC.AIType` | Field aiType renamed to AIType in 1.4 |
| `Terraria.ModLoader.ModNPC.animationType` | `Terraria.ModLoader.ModNPC.AnimationType` | Field animationType renamed to AnimationType in 1.4 |
| `Terraria.ModLoader.ModNPC.music` | `Terraria.ModLoader.ModNPC.Music` | Field music renamed to Music in 1.4 |
| `Terraria.ModLoader.ModNPC.musicPriority` | `Terraria.ModLoader.ModNPC.SceneEffectPriority` | Field musicPriority renamed to SceneEffectPriority in 1.4 |
| `Terraria.ModLoader.ModNPC.drawOffsetY` | `Terraria.ModLoader.ModNPC.DrawOffsetY` | Field drawOffsetY renamed to DrawOffsetY in 1.4 |
| `Terraria.ModLoader.ModNPC.banner` | `Terraria.ModLoader.ModNPC.Banner` | Field banner renamed to Banner in 1.4 |
| `Terraria.ModLoader.ModNPC.bannerItem` | `Terraria.ModLoader.ModNPC.BannerItem` | Field bannerItem renamed to BannerItem in 1.4 |

---

## 2. MINIMAL WORKING BOILERPLATES

### Sword (Melee Weapon)
```csharp
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.Content.Items
{
    public class MySword : ModItem
    {
        public override void SetDefaults()
        {
            Item.width = 40;
            Item.height = 40;
            Item.useStyle = ItemUseStyleID.Swing;
            Item.useTime = 20;
            Item.useAnimation = 20;
            Item.autoReuse = true;
            Item.DamageType = DamageClass.Melee;
            Item.damage = 25;
            Item.knockBack = 4f;
            Item.value = Item.buyPrice(silver: 50);
            Item.rare = ItemRarityID.Green;
            Item.UseSound = SoundID.Item1;
        }

        public override void OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone)
        {
            target.AddBuff(BuffID.OnFire, 180);
        }

        public override void AddRecipes()
        {
            CreateRecipe()
                .AddIngredient(ItemID.Wood, 10)
                .AddTile(TileID.WorkBenches)
                .Register();
        }
    }
}
```

### Accessory
```csharp
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.Content.Items
{
    public class SpeedBooster : ModItem
    {
        public override void SetDefaults()
        {
            Item.width = 24;
            Item.height = 24;
            Item.accessory = true;
            Item.rare = ItemRarityID.Orange;
            Item.value = Item.buyPrice(gold: 1);
        }

        public override void UpdateAccessory(Player player, bool hideVisual)
        {
            player.moveSpeed += 0.20f;
            player.buffImmune[BuffID.Chilled] = true;
        }
    }
}
```

### Localization (`Localization/en-US.hjson`)
1.4 uses HJSON for automatic item name & tooltip localization. Never hardcode DisplayNames in code:
```hjson
Mods: {
    MyMod: {
        ItemName: {
            MySword: "My Flame Sword"
            SpeedBooster: "Sprint Emblem"
        }
        ItemTooltip: {
            MySword: "Ignites foes on hit"
            SpeedBooster: "Increases movement speed by 20% and grants immunity to Chilled"
        }
    }
}
```

---

## 3. PRIMARY HOOKS REFERENCE (EXTRACTED FROM DECOMPILED DLL)

### `ModItem` (`Terraria.ModLoader.ModItem`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AddRecipes` | `void AddRecipes()` | Override this method to add |
| `AllowPrefix` | `bool AllowPrefix(int pre)` |  |
| `AltFunctionUse` | `bool AltFunctionUse(Player player)` |  |
| `AnglerQuestChat` | `void AnglerQuestChat(ref string description, ref string catchLocation)` |  |
| `ApplyPotionDelay` | `bool ApplyPotionDelay(Player player, int potionDelay)` |  |
| `ApplyPrefix` | `void ApplyPrefix(int pre)` |  |
| `ArmorArmGlowMask` | `void ArmorArmGlowMask(Player drawPlayer, float shadow, ref int glowMask, ref Color color)` |  |
| `ArmorSetShadows` | `void ArmorSetShadows(Player player)` |  |
| `AutoDefaults` | `void AutoDefaults()` | Automatically sets certain defaults. Override this if you do not want the proper |
| `AutoStaticDefaults` | `void AutoStaticDefaults()` | Automatically sets certain static defaults. Override this if you do not want the |
| `CanAccessoryBeEquippedWith` | `bool CanAccessoryBeEquippedWith(Item equippedItem, Item incomingItem, Player player)` |  |
| `CanAutoReuseItem` | `bool? CanAutoReuseItem(Player player)` |  |
| `CanBeChosenAsAmmo` | `bool? CanBeChosenAsAmmo(Item weapon, Player player)` |  |
| `CanBeConsumedAsAmmo` | `bool CanBeConsumedAsAmmo(Item weapon, Player player)` |  |
| `CanCatchNPC` | `bool? CanCatchNPC(NPC target, Player player)` |  |

### `ModNPC` (`Terraria.ModLoader.ModNPC`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AI` | `void AI()` | Allows you to determine how this NPC behaves. This will only be called if PreAI  |
| `AddShops` | `void AddShops()` | Allows you to add shops to this NPC, similar to adding recipes for items. |
| `ApplyDifficultyAndPlayerScaling` | `void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment)` |  |
| `AutoStaticDefaults` | `void AutoStaticDefaults()` | Automatically sets certain static defaults. Override this if you do not want the |
| `BossHeadRotation` | `void BossHeadRotation(ref float rotation)` |  |
| `BossHeadSlot` | `void BossHeadSlot(ref int index)` |  |
| `BossHeadSpriteEffects` | `void BossHeadSpriteEffects(ref SpriteEffects spriteEffects)` |  |
| `BossLoot` | `void BossLoot(ref int potionType)` |  |
| `CanBeCaughtBy` | `bool? CanBeCaughtBy(Item item, Player player)` |  |
| `CanBeHitByItem` | `bool? CanBeHitByItem(Player player, Item item)` |  |
| `CanBeHitByNPC` | `bool CanBeHitByNPC(NPC attacker)` |  |
| `CanBeHitByProjectile` | `bool? CanBeHitByProjectile(Projectile projectile)` |  |
| `CanChat` | `bool CanChat()` | Allows you to determine whether this NPC can talk with the player. By default, r |
| `CanCollideWithPlayerMeleeAttack` | `bool? CanCollideWithPlayerMeleeAttack(Player player, Item item, Rectangle meleeAttackHitbox)` |  |
| `CanFallThroughPlatforms` | `bool? CanFallThroughPlatforms()` | Allows you to determine how and when this NPC can fall through platforms and sim |

### `ModProjectile` (`Terraria.ModLoader.ModProjectile`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AI` | `void AI()` | Allows you to determine how this projectile behaves. This will only be called if |
| `AutoStaticDefaults` | `void AutoStaticDefaults()` | Automatically sets certain static defaults. Override this if you do not want the |
| `CanCutTiles` | `bool? CanCutTiles()` | Return true or false to specify if the projectile can cut tiles like vines, pots |
| `CanDamage` | `bool? CanDamage()` | Whether or not this projectile is capable of killing tiles (such as grass) and d |
| `CanHitNPC` | `bool? CanHitNPC(NPC target)` |  |
| `CanHitPlayer` | `bool CanHitPlayer(Player target)` |  |
| `CanHitPvp` | `bool CanHitPvp(Player target)` |  |
| `CanUseGrapple` | `bool? CanUseGrapple(Player player)` |  |
| `Colliding` | `bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox)` |  |
| `CutTiles` | `void CutTiles()` | Code ran when the projectile cuts tiles. Only runs if CanCutTiles() returns true |
| `DrawBehind` | `void DrawBehind(int index, List<int> behindNPCsAndTiles, List<int> behindNPCs, List<int> behindProjectiles, List<int> overPlayers, List<int> overWiresUI)` |  |
| `EmitEnchantmentVisualsAt` | `void EmitEnchantmentVisualsAt(Vector2 boxPosition, int boxWidth, int boxHeight)` |  |
| `FlailSpinCollisionRange` | `void FlailSpinCollisionRange(ref float range)` |  |
| `FlailStats` | `void FlailStats(ref int launchTimeLimit, ref float launchSpeed, ref float maxLaunchLength, ref float retractAcceleration, ref float maxRetractSpeed, ref float forcedRetractAcceleration, ref float maxForcedRetractSpeed, ref int ricochetTimeLimit, ref float spinVisualDistance)` |  |
| `GetAlpha` | `Color? GetAlpha(Color lightColor)` |  |

### `ModBuff` (`Terraria.ModLoader.ModBuff`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `ModifyBuffText` | `void ModifyBuffText(ref string buffName, ref string tip, ref int rare)` |  |
| `PostDraw` | `void PostDraw(SpriteBatch spriteBatch, int buffIndex, BuffDrawParams drawParams)` |  |
| `PreDraw` | `bool PreDraw(SpriteBatch spriteBatch, int buffIndex, ref BuffDrawParams drawParams)` |  |
| `ReApply` | `bool ReApply(NPC npc, int time, int buffIndex)` |  |
| `RightClick` | `bool RightClick(int buffIndex)` |  |
| `Update` | `void Update(NPC npc, ref int buffIndex)` |  |

### `ModTile` (`Terraria.ModLoader.ModTile`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AdjustMultiTileVineParameters` | `void AdjustMultiTileVineParameters(int i, int j, ref float? overrideWindCycle, ref float windPushPowerX, ref float windPushPowerY, ref bool dontRotateTopTiles, ref float totalWindMultiplier, ref Texture2D glowTexture, ref Color glowColor)` |  |
| `AnimateIndividualTile` | `void AnimateIndividualTile(int type, int i, int j, ref int frameXOffset, ref int frameYOffset)` |  |
| `AnimateTile` | `void AnimateTile(ref int frame, ref int frameCounter)` |  |
| `AutoSelect` | `bool AutoSelect(int i, int j, Item item)` |  |
| `CanDrop` | `bool CanDrop(int i, int j)` |  |
| `CanKillTile` | `bool CanKillTile(int i, int j, ref bool blockDamaged)` |  |
| `CanReplace` | `bool CanReplace(int i, int j, int tileTypeBeingPlaced)` |  |
| `ChangeWaterfallStyle` | `void ChangeWaterfallStyle(ref int style)` |  |
| `DefaultContainerName` | `LocalizedText DefaultContainerName(int frameX, int frameY)` |  |
| `DrawEffects` | `void DrawEffects(int i, int j, SpriteBatch spriteBatch, ref TileDrawInfo drawData)` |  |
| `DropCritterChance` | `void DropCritterChance(int i, int j, ref int wormChance, ref int grassHopperChance, ref int jungleGrubChance)` |  |
| `EmitParticles` | `void EmitParticles(int i, int j, Tile tile, short tileFrameX, short tileFrameY, Color tileLight, bool visible)` |  |
| `FloorVisuals` | `void FloorVisuals(Player player)` |  |
| `GetItemDrops` | `IEnumerable<Item> GetItemDrops(int i, int j)` |  |
| `GetTileFlameData` | `void GetTileFlameData(int i, int j, ref TileDrawing.TileFlameData tileFlameData)` |  |

### `GlobalItem` (`Terraria.ModLoader.GlobalItem`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AddRecipes` | `void AddRecipes()` | Override this method to add |
| `AllowPrefix` | `bool AllowPrefix(Item item, int pre)` |  |
| `AltFunctionUse` | `bool AltFunctionUse(Item item, Player player)` |  |
| `AnglerChat` | `void AnglerChat(int type, ref string chat, ref string catchLocation)` |  |
| `ApplyPotionDelay` | `bool ApplyPotionDelay(Item item, Player player, int potionDelay)` |  |
| `ApplyPrefix` | `void ApplyPrefix(Item item, int pre)` |  |
| `ArmorArmGlowMask` | `void ArmorArmGlowMask(int slot, Player drawPlayer, float shadow, ref int glowMask, ref Color color)` |  |
| `ArmorSetShadows` | `void ArmorSetShadows(Player player, string set)` |  |
| `CanAccessoryBeEquippedWith` | `bool CanAccessoryBeEquippedWith(Item equippedItem, Item incomingItem, Player player)` |  |
| `CanAutoReuseItem` | `bool? CanAutoReuseItem(Item item, Player player)` |  |
| `CanBeChosenAsAmmo` | `bool? CanBeChosenAsAmmo(Item ammo, Item weapon, Player player)` |  |
| `CanBeConsumedAsAmmo` | `bool CanBeConsumedAsAmmo(Item ammo, Item weapon, Player player)` |  |
| `CanCatchNPC` | `bool? CanCatchNPC(Item item, NPC target, Player player)` |  |
| `CanChooseAmmo` | `bool? CanChooseAmmo(Item weapon, Item ammo, Player player)` |  |
| `CanConsumeAmmo` | `bool CanConsumeAmmo(Item weapon, Item ammo, Player player)` |  |

### `GlobalNPC` (`Terraria.ModLoader.GlobalNPC`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AI` | `void AI(NPC npc)` |  |
| `ApplyDifficultyAndPlayerScaling` | `void ApplyDifficultyAndPlayerScaling(NPC npc, int numPlayers, float balance, float bossAdjustment)` |  |
| `BossHeadRotation` | `void BossHeadRotation(NPC npc, ref float rotation)` |  |
| `BossHeadSlot` | `void BossHeadSlot(NPC npc, ref int index)` |  |
| `BossHeadSpriteEffects` | `void BossHeadSpriteEffects(NPC npc, ref SpriteEffects spriteEffects)` |  |
| `BuffTownNPC` | `void BuffTownNPC(ref float damageMult, ref int defense)` |  |
| `CanBeCaughtBy` | `bool? CanBeCaughtBy(NPC npc, Item item, Player player)` |  |
| `CanBeHitByItem` | `bool? CanBeHitByItem(NPC npc, Player player, Item item)` |  |
| `CanBeHitByNPC` | `bool CanBeHitByNPC(NPC npc, NPC attacker)` |  |
| `CanBeHitByProjectile` | `bool? CanBeHitByProjectile(NPC npc, Projectile projectile)` |  |
| `CanChat` | `bool? CanChat(NPC npc)` |  |
| `CanCollideWithPlayerMeleeAttack` | `bool? CanCollideWithPlayerMeleeAttack(NPC npc, Player player, Item item, Rectangle meleeAttackHitbox)` |  |
| `CanFallThroughPlatforms` | `bool? CanFallThroughPlatforms(NPC npc)` |  |
| `CanGoToStatue` | `bool? CanGoToStatue(NPC npc, bool toKingStatue)` |  |
| `CanHitNPC` | `bool CanHitNPC(NPC npc, NPC target)` |  |

### `ModPlayer` (`Terraria.ModLoader.ModPlayer`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AddMaterialsForCrafting` | `IEnumerable<Item> AddMaterialsForCrafting(out ItemConsumedCallback itemConsumedCallback)` |  |
| `AddStartingItems` | `IEnumerable<Item> AddStartingItems(bool mediumCoreDeath)` |  |
| `AnglerQuestReward` | `void AnglerQuestReward(float rareMultiplier, List<Item> rewardItems)` |  |
| `ApplyPotionDelay` | `bool ApplyPotionDelay(Item item, int potionDelay)` |  |
| `ArmorSetBonusActivated` | `void ArmorSetBonusActivated()` | This is called when the player activates their armor set bonus by double tapping |
| `ArmorSetBonusHeld` | `void ArmorSetBonusHeld(int holdTime)` |  |
| `CanAutoReuseItem` | `bool? CanAutoReuseItem(Item item)` |  |
| `CanBeHitByNPC` | `bool CanBeHitByNPC(NPC npc, ref int cooldownSlot)` |  |
| `CanBeHitByProjectile` | `bool CanBeHitByProjectile(Projectile proj)` |  |
| `CanBeTeleportedTo` | `bool CanBeTeleportedTo(Vector2 teleportPosition, string context)` |  |
| `CanBuyItem` | `bool CanBuyItem(NPC vendor, Item[] shopInventory, Item item)` |  |
| `CanCatchNPC` | `bool? CanCatchNPC(NPC target, Item item)` |  |
| `CanConsumeAmmo` | `bool CanConsumeAmmo(Item weapon, Item ammo)` |  |
| `CanConsumeBait` | `bool? CanConsumeBait(Item bait)` |  |
| `CanHitNPC` | `bool CanHitNPC(NPC target)` |  |

### `ModSystem` (`Terraria.ModLoader.ModSystem`)
| Hook Name | Signature | Summary |
| :--- | :--- | :--- |
| `AddRecipeGroups` | `void AddRecipeGroups()` | Override this method to add recipe groups to the game. |
| `AddRecipes` | `void AddRecipes()` | Override this method to add |
| `CanWorldBePlayed` | `bool CanWorldBePlayed(PlayerFileData playerData, WorldFileData worldFileData)` |  |
| `ClearWorld` | `void ClearWorld()` | Called whenever the world is cleared. Use this to reset world-related data struc |
| `HijackGetData` | `bool HijackGetData(ref byte messageType, ref BinaryReader reader, int playerNumber)` |  |
| `HijackSendData` | `bool HijackSendData(int whoAmI, int msgType, int remoteClient, int ignoreClient, NetworkText text, int number, float number2, float number3, float number4, int number5, int number6, int number7)` |  |
| `LoadWorldData` | `void LoadWorldData(TagCompound tag)` |  |
| `ModifyGameTipVisibility` | `void ModifyGameTipVisibility(IReadOnlyList<GameTipData> gameTips)` |  |
| `ModifyHardmodeTasks` | `void ModifyHardmodeTasks(List<GenPass> list)` |  |
| `ModifyInterfaceLayers` | `void ModifyInterfaceLayers(List<GameInterfaceLayer> layers)` |  |
| `ModifyLightingBrightness` | `void ModifyLightingBrightness(ref float scale)` |  |
| `ModifyScreenPosition` | `void ModifyScreenPosition()` | Use this hook to modify |
| `ModifySunLightColor` | `void ModifySunLightColor(ref Color tileColor, ref Color backgroundColor)` |  |
| `ModifyTimeRate` | `void ModifyTimeRate(ref double timeRate, ref double tileUpdateRate, ref double eventUpdateRate)` |  |
| `ModifyTransformMatrix` | `void ModifyTransformMatrix(ref SpriteViewMatrix Transform)` |  |
