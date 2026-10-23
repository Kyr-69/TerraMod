#!/usr/bin/env python3
import os
import json
import sqlite3

DB_PATH = '/home/Kyr/projects/teramod/tmod_1_4.db'

UI_CLASSES = [
    {
        "id": "Terraria.UI.UIState",
        "name": "UIState",
        "label": "Class",
        "data": {
            "namespace": "Terraria.UI",
            "summary": "Represents a distinct user interface screen or state containing a hierarchy of UIElements.",
            "inherits": "Terraria.UI.UIElement"
        }
    },
    {
        "id": "Terraria.UI.UserInterface",
        "name": "UserInterface",
        "label": "Class",
        "data": {
            "namespace": "Terraria.UI",
            "summary": "Manages and updates the active UIState, handles input dispatch, and coordinates rendering."
        }
    },
    {
        "id": "Terraria.UI.UIElement",
        "name": "UIElement",
        "label": "Class",
        "data": {
            "namespace": "Terraria.UI",
            "summary": "Base class for all visual and interactive UI components in Terraria. Handles layout, positioning, clipping, and mouse events."
        }
    },
    {
        "id": "Terraria.GameContent.UI.Elements.UIPanel",
        "name": "UIPanel",
        "label": "Class",
        "data": {
            "namespace": "Terraria.GameContent.UI.Elements",
            "summary": "Standard 9-sliced panel container with customizable border and background colors.",
            "inherits": "Terraria.UI.UIElement"
        }
    },
    {
        "id": "Terraria.GameContent.UI.Elements.UIText",
        "name": "UIText",
        "label": "Class",
        "data": {
            "namespace": "Terraria.GameContent.UI.Elements",
            "summary": "Renders localized or dynamic text strings with scaling and color styling.",
            "inherits": "Terraria.UI.UIElement"
        }
    },
    {
        "id": "Terraria.GameContent.UI.Elements.UIImage",
        "name": "UIImage",
        "label": "Class",
        "data": {
            "namespace": "Terraria.GameContent.UI.Elements",
            "summary": "Renders static or sprite sheet textures with custom framing.",
            "inherits": "Terraria.UI.UIElement"
        }
    },
    {
        "id": "Terraria.GameContent.UI.Elements.UIList",
        "name": "UIList",
        "label": "Class",
        "data": {
            "namespace": "Terraria.GameContent.UI.Elements",
            "summary": "Scrollable list container for dynamic child elements with scrollbar binding.",
            "inherits": "Terraria.UI.UIElement"
        }
    },
    {
        "id": "Terraria.GameContent.UI.Elements.UIScrollbar",
        "name": "UIScrollbar",
        "label": "Class",
        "data": {
            "namespace": "Terraria.GameContent.UI.Elements",
            "summary": "Interactive scrollbar widget for scrolling UIList containers.",
            "inherits": "Terraria.UI.UIElement"
        }
    }
]

UI_HOOKS = [
    # UIState hooks
    {
        "class_id": "Terraria.UI.UIState",
        "id": "Terraria.UI.UIState.OnInitialize",
        "name": "OnInitialize",
        "signature": "public virtual void OnInitialize()",
        "return_type": "void",
        "params": "",
        "summary": "Called once when the UIState is first initialized. Construct and Append children elements here."
    },
    {
        "class_id": "Terraria.UI.UIState",
        "id": "Terraria.UI.UIState.OnActivate",
        "name": "OnActivate",
        "signature": "public virtual void OnActivate()",
        "return_type": "void",
        "params": "",
        "summary": "Called whenever SetState activates this UIState."
    },
    {
        "class_id": "Terraria.UI.UIState",
        "id": "Terraria.UI.UIState.OnDeactivate",
        "name": "OnDeactivate",
        "signature": "public virtual void OnDeactivate()",
        "return_type": "void",
        "params": "",
        "summary": "Called whenever this UIState is deactivated, swapped out, or hidden."
    },
    {
        "class_id": "Terraria.UI.UIState",
        "id": "Terraria.UI.UIState.Draw",
        "name": "Draw",
        "signature": "public virtual void Draw(SpriteBatch spriteBatch)",
        "return_type": "void",
        "params": "SpriteBatch spriteBatch",
        "summary": "Draws this UIState and propagates draw calls to all visible children."
    },
    {
        "class_id": "Terraria.UI.UIState",
        "id": "Terraria.UI.UIState.Update",
        "name": "Update",
        "signature": "public virtual void Update(GameTime gameTime)",
        "return_type": "void",
        "params": "GameTime gameTime",
        "summary": "Updates UI state logic, animations, and input timers."
    },
    # UserInterface hooks
    {
        "class_id": "Terraria.UI.UserInterface",
        "id": "Terraria.UI.UserInterface.SetState",
        "name": "SetState",
        "signature": "public void SetState(UIState state)",
        "return_type": "void",
        "params": "UIState state",
        "summary": "Changes active UIState. Pass null to hide the interface."
    },
    {
        "class_id": "Terraria.UI.UserInterface",
        "id": "Terraria.UI.UserInterface.Update",
        "name": "Update",
        "signature": "public void Update(GameTime gameTime)",
        "return_type": "void",
        "params": "GameTime gameTime",
        "summary": "Propagates update ticks to the active UIState and handles mouse events."
    },
    {
        "class_id": "Terraria.UI.UserInterface",
        "id": "Terraria.UI.UserInterface.Draw",
        "name": "Draw",
        "signature": "public void Draw(SpriteBatch spriteBatch, GameTime time)",
        "return_type": "void",
        "params": "SpriteBatch spriteBatch, GameTime time",
        "summary": "Draws the current active UIState into the sprite batch."
    },
    {
        "class_id": "Terraria.UI.UserInterface",
        "id": "Terraria.UI.UserInterface.IsElementUnderMouse",
        "name": "IsElementUnderMouse",
        "signature": "public bool IsElementUnderMouse()",
        "return_type": "bool",
        "params": "",
        "summary": "Returns true if the mouse cursor is currently hovering over any child UI element in the active state."
    },
    # UIElement hooks
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.Append",
        "name": "Append",
        "signature": "public void Append(UIElement element)",
        "return_type": "void",
        "params": "UIElement element",
        "summary": "Adds a child element to this element's hierarchy."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.Remove",
        "name": "Remove",
        "signature": "public void Remove()",
        "return_type": "void",
        "params": "",
        "summary": "Removes this element from its parent hierarchy."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.GetDimensions",
        "name": "GetDimensions",
        "signature": "public CalculatedStyle GetDimensions()",
        "return_type": "CalculatedStyle",
        "params": "",
        "summary": "Returns the outer calculated screen rectangle (Position, Size, Bounds) for this element."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.GetInnerDimensions",
        "name": "GetInnerDimensions",
        "signature": "public CalculatedStyle GetInnerDimensions()",
        "return_type": "CalculatedStyle",
        "params": "",
        "summary": "Returns the inner calculated dimensions (excluding padding and borders)."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.DrawSelf",
        "name": "DrawSelf",
        "signature": "protected virtual void DrawSelf(SpriteBatch spriteBatch)",
        "return_type": "void",
        "params": "SpriteBatch spriteBatch",
        "summary": "Virtual method to custom draw this specific element. Call base.DrawSelf(spriteBatch) when inheriting UIPanel."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.LeftMouseDown",
        "name": "LeftMouseDown",
        "signature": "public virtual void LeftMouseDown(UIMouseEvent evt)",
        "return_type": "void",
        "params": "UIMouseEvent evt",
        "summary": "Called when mouse left button is clicked down on this element."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.LeftMouseUp",
        "name": "LeftMouseUp",
        "signature": "public virtual void LeftMouseUp(UIMouseEvent evt)",
        "return_type": "void",
        "params": "UIMouseEvent evt",
        "summary": "Called when mouse left button is released on this element."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.MouseOver",
        "name": "MouseOver",
        "signature": "public virtual void MouseOver(UIMouseEvent evt)",
        "return_type": "void",
        "params": "UIMouseEvent evt",
        "summary": "Called when mouse begins hovering over this element."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.MouseOut",
        "name": "MouseOut",
        "signature": "public virtual void MouseOut(UIMouseEvent evt)",
        "return_type": "void",
        "params": "UIMouseEvent evt",
        "summary": "Called when mouse leaves this element's bounds."
    },
    {
        "class_id": "Terraria.UI.UIElement",
        "id": "Terraria.UI.UIElement.Recalculate",
        "name": "Recalculate",
        "signature": "public virtual void Recalculate()",
        "return_type": "void",
        "params": "",
        "summary": "Forces recalculation of pixel and percentage coordinates for this element and all its children."
    }
]

UI_SNIPPETS = [
    {
        "id": "snippet:UI_CustomHUD",
        "name": "UI_CustomHUD",
        "data": {
            "file": "Common/UI/CustomHUD.cs",
            "summary": "Complete 1.4 custom resource gauge or HUD with UIState, UIPanel, UIText, and gradient fill",
            "code": """using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.GameContent.UI.Elements;
using Terraria.UI;

namespace MyMod.Common.UI
{
    public class CustomHUDState : UIState
    {
        private UIPanel panel;
        private UIText text;

        public override void OnInitialize()
        {
            panel = new UIPanel();
            panel.Left.Set(20, 0f);
            panel.Top.Set(100, 0f);
            panel.Width.Set(200, 0f);
            panel.Height.Set(60, 0f);
            panel.BackgroundColor = new Color(30, 30, 60, 200);
            
            text = new UIText("Resource: 100 / 100", 0.9f);
            text.HAlign = 0.5f;
            text.VAlign = 0.5f;
            panel.Append(text);
            
            Append(panel);
        }

        public override void Update(GameTime gameTime)
        {
            base.Update(gameTime);
            if (panel.ContainsPoint(Main.MouseScreen))
            {
                Main.LocalPlayer.mouseInterface = true;
            }
            text.SetText($"Health: {Main.LocalPlayer.statLife} / {Main.LocalPlayer.statLifeMax2}");
        }
    }
}"""
        }
    },
    {
        "id": "snippet:UISystem_LayerInjection",
        "name": "UISystem_LayerInjection",
        "data": {
            "file": "Common/UI/CustomUISystem.cs",
            "summary": "Standard ModSystem layer injection pattern with UserInterface, ModifyInterfaceLayers, and UpdateUI",
            "code": """using Microsoft.Xna.Framework;
using System.Collections.Generic;
using Terraria;
using Terraria.ModLoader;
using Terraria.UI;

namespace MyMod.Common.UI
{
    [Autoload(Side = ModSide.Client)]
    public class CustomUISystem : ModSystem
    {
        private UserInterface customUserInterface;
        internal CustomHUDState customHUDState;

        public override void Load()
        {
            customUserInterface = new UserInterface();
            customHUDState = new CustomHUDState();
            customHUDState.Activate();
            customUserInterface.SetState(customHUDState);
        }

        public override void Unload()
        {
            customHUDState = null;
            customUserInterface = null;
        }

        public override void UpdateUI(GameTime gameTime)
        {
            if (customUserInterface?.CurrentState != null)
            {
                customUserInterface.Update(gameTime);
            }
        }

        public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers)
        {
            int mouseTextIndex = layers.FindIndex(layer => layer.Name.Equals("Vanilla: Mouse Text"));
            if (mouseTextIndex != -1)
            {
                layers.Insert(mouseTextIndex, new LegacyGameInterfaceLayer(
                    "MyMod: Custom HUD",
                    delegate
                    {
                        if (customUserInterface?.CurrentState != null)
                        {
                            customUserInterface.Draw(Main.spriteBatch, new GameTime());
                        }
                        return true;
                    },
                    InterfaceScaleType.UI
                ));
            }
        }
    }
}"""
        }
    },
    {
        "id": "snippet:UI_DraggablePanel",
        "name": "UI_DraggablePanel",
        "data": {
            "file": "Common/UI/DraggableUIPanel.cs",
            "summary": "Draggable UIPanel handling mouse down, drag offset, mouseInterface locking, and screen boundary clamping",
            "code": """using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent.UI.Elements;
using Terraria.UI;

namespace MyMod.Common.UI
{
    public class DraggableUIPanel : UIPanel
    {
        private Vector2 offset;
        private bool dragging;

        public override void LeftMouseDown(UIMouseEvent evt)
        {
            base.LeftMouseDown(evt);
            if (evt.Target == this)
            {
                offset = new Vector2(evt.MousePosition.X - Left.Pixels, evt.MousePosition.Y - Top.Pixels);
                dragging = true;
            }
        }

        public override void LeftMouseUp(UIMouseEvent evt)
        {
            base.LeftMouseUp(evt);
            if (evt.Target == this)
            {
                dragging = false;
                Left.Set(evt.MousePosition.X - offset.X, 0f);
                Top.Set(evt.MousePosition.Y - offset.Y, 0f);
                Recalculate();
            }
        }

        public override void Update(GameTime gameTime)
        {
            base.Update(gameTime);
            if (ContainsPoint(Main.MouseScreen))
            {
                Main.LocalPlayer.mouseInterface = true;
            }
            if (dragging)
            {
                Left.Set(Main.mouseX - offset.X, 0f);
                Top.Set(Main.mouseY - offset.Y, 0f);
                Recalculate();
            }
        }
    }
}"""
        }
    }
]

def populate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Insert classes
    for c in UI_CLASSES:
        cur.execute("INSERT OR REPLACE INTO nodes (id, label, name, data) VALUES (?, ?, ?, ?)",
                    (c['id'], c['label'], c['name'], json.dumps(c['data'])))
                    
    # Insert hooks and edges
    for h in UI_HOOKS:
        hook_data = {
            "signature": h['signature'],
            "return_type": h['return_type'],
            "params": h['params'],
            "summary": h['summary']
        }
        cur.execute("INSERT OR REPLACE INTO nodes (id, label, name, data) VALUES (?, ?, ?, ?)",
                    (h['id'], 'Hook', h['name'], json.dumps(hook_data)))
        cur.execute("INSERT OR REPLACE INTO edges (source_id, target_id, relationship) VALUES (?, ?, 'EXPOSES_HOOK')",
                    (h['class_id'], h['id']))
                    
    # Update ModSystem.ModifyInterfaceLayers & UpdateUI summaries if present
    cur.execute("SELECT data FROM nodes WHERE id = 'Terraria.ModLoader.ModSystem.ModifyInterfaceLayers'")
    row = cur.fetchone()
    if row:
        d = json.loads(row[0])
        d['summary'] = "Injects custom UI rendering layers into Terraria's rendering pipeline. Locate 'Vanilla: Mouse Text' index and insert a new LegacyGameInterfaceLayer with InterfaceScaleType.UI."
        cur.execute("UPDATE nodes SET data = ? WHERE id = 'Terraria.ModLoader.ModSystem.ModifyInterfaceLayers'", (json.dumps(d),))
        
    cur.execute("SELECT data FROM nodes WHERE id = 'Terraria.ModLoader.ModSystem.UpdateUI'")
    row = cur.fetchone()
    if row:
        d = json.loads(row[0])
        d['summary'] = "Called every client frame to update active UserInterface instances. Call customUserInterface?.Update(gameTime)."
        cur.execute("UPDATE nodes SET data = ? WHERE id = 'Terraria.ModLoader.ModSystem.UpdateUI'", (json.dumps(d),))
        
    # Insert snippets
    for s in UI_SNIPPETS:
        cur.execute("INSERT OR REPLACE INTO nodes (id, label, name, data) VALUES (?, ?, ?, ?)",
                    (s['id'], 'Snippet', s['name'], json.dumps(s['data'])))
                    
    conn.commit()
    
    # Verify
    cur.execute("SELECT count(*) FROM nodes WHERE id LIKE 'Terraria.UI.%'")
    print(f"Added UI nodes: {cur.fetchone()[0]}")
    cur.execute("SELECT count(*) FROM nodes WHERE label = 'Snippet' AND (name LIKE '%UI%' OR name LIKE '%HUD%')")
    print(f"UI Snippets count: {cur.fetchone()[0]}")
    conn.close()

if __name__ == '__main__':
    populate()
